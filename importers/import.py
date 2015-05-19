"""
Run this script inside the campaign directory you want to import.

Expects campaign structure as

Campaign Directory
  |--campaign.txt
  |--Deployment Directory
  |       |--description.txt
  |       |--images.csv
  |       |--images01.jpg
  |       |--images02.jpg
  |       |-- ...
  |--Deployment Directory
  |       |--description.txt
  |       |--images.csv
  |       |--images01.jpg
  |       |--images02.jpg
  |       |-- ...
  ...

"""

import sys
sys.path.append('/home/benthobox/benthobox')

import os

# Bind to django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "benthobox.settings")
#os.environ['DJANGO_SETTINGS_MODULE'] ='benthobox.settings'
from django.conf import settings

#from django.core.management import setup_environ

from benthobox import settings
from catamidb.models import *
from catamidb import authorization

#setup_environ(settings)

import os.path
import argparse
import csv
import json
import numpy as np
import time

from PIL import Image as PILImage

#Filenames for critical campaign/deployment files
images_filename = 'images.csv'
description_filename = 'description.txt'
campaign_filename = 'campaign.txt'


def read_campaign(root_import_path):
    """ reads campaign.txt and returns contents in a dict
    """
    if os.path.isfile(os.path.join(root_import_path, campaign_filename)):
        # any missing **required** fields will make this false. spawns MISSING error. Fatal.
        #is_complete = True

        # any missing data will make this false. spawns a warning.
        #is_minally_ok = True

        # True if something wierd happens
        is_broken = False  # True if something wierd happens. Fatal

        version = ''
        name = ''
        description_text = ''
        assoc_researchers_text = ''
        assoc_publications_text = ''
        assoc_research_grants_text = ''
        start_date_text = ''
        end_date_text = ''
        contact_person_text = ''

        f = open(os.path.join(root_import_path, campaign_filename))

        for line in f.readlines():

            split_string = line.rstrip().split(':')

            if split_string[0].lower() == 'Version'.lower():
                version = split_string[1]
            elif split_string[0].lower() == 'Name'.lower():
                name = split_string[1]
            elif split_string[0].lower() == 'Description'.lower():
                description_text = split_string[1]
            elif split_string[0].lower() == 'Associated Researchers'.lower():
                assoc_researchers_text = split_string[1]
            elif split_string[0].lower() == 'Associated Publications'.lower():
                assoc_publications_text = split_string[1]
            elif split_string[0].lower() == 'Associated Research Grants'.lower():
                assoc_research_grants_text = split_string[1]
            elif split_string[0].lower() == 'Start Date'.lower():
                start_date_text = split_string[1]
            elif split_string[0].lower() == 'End Date'.lower():
                end_date_text = split_string[1]
            elif split_string[0].lower() == 'Contact Person'.lower():
                contact_person_text = split_string[1]
            else:
                print 'ERROR: Unknown label in campaign file;', split_string[0]
                is_broken = True

        campaign_data = dict(#version=version,
                             short_name=name,
                             description=description_text,
                             associated_researchers=assoc_researchers_text,
                             associated_publications=assoc_publications_text,
                             associated_research_grant=assoc_research_grants_text,
                             date_start=start_date_text.strip(),
                             date_end=end_date_text.strip(),
                             contact_person=contact_person_text)
        return campaign_data

    else:
        print "ERROR: Can not open the campaign.txt file."

    return False


def read_deployment_file(deployment_path, image_data):
    """reads the description.txt file for the specified deployment
    """



    deployment_info = {}
    if os.path.isfile(os.path.join(deployment_path, description_filename)):
        f = open(os.path.join(deployment_path, description_filename))

        type = ""
        description = ""
        operator = ""
        keywords = ""

        # get the details from the descriptor file
        for line in f.readlines():
            split_string = line.rstrip().split(':')
            #if split_string[0].lower() == 'Version'.lower():
            #    deployment_info['version'] = split_string[1].strip()
            if split_string[0].lower() == 'Type'.lower():
                type = split_string[1].strip()
            elif split_string[0].lower() == 'Description'.lower():
                description = split_string[1]
            elif split_string[0].lower() == 'Operator'.lower():
                operator = split_string[1]
            elif split_string[0].lower() == 'Keywords'.lower():
                keywords = split_string[1]

        # pull out extra information
        # need to find the first image with a lat long
        first_valid_image = None

        for im in image_data:
            if (im['latitude'] is not None and str(im['latitude']) != 'None') and (im['longitude'] is not None and str(im['latitude']) != 'None'):
                    first_valid_image = im
                    break

        if first_valid_image is None:
            # somehow we got here after all that validation. have to abort. something bad has happened.
            return None

        depth_data_temp = []
        latitude_data_temp = []
        longitude_data_temp = []
        for im in image_data:
            if im['latitude'] is not None and str(im['latitude']) != 'None':
                latitude_data_temp.append(float(im['latitude']))
            if im['longitude'] is not None and str(im['longitude']) != 'None':
                longitude_data_temp.append(float(im['longitude']))
            if im['depth'] is not None and str(im['depth']) != 'None':
                depth_data_temp.append(float(im['depth']))

        depth_array = np.array(depth_data_temp, dtype=float)
        latitude_array = np.array(latitude_data_temp, dtype=float)
        longitude_array = np.array(longitude_data_temp, dtype=float)

        bounding_polygon = 'SRID=4326;POLYGON(('+str(longitude_array.min())+' '+str(latitude_array.min())+','\
            + str(longitude_array.max())+' '+str(latitude_array.min())+','\
            + str(longitude_array.max())+' '+str(latitude_array.max())+','\
            + str(longitude_array.min())+' '+str(latitude_array.max())+','\
            + str(longitude_array.min())+' '+str(latitude_array.min())+'))'

        #note that geo arguments are very picky about internal space characters (only between long/lat pairs)
        #note also: geo order is long/lat
        start_position = 'SRID=4326;POINT('+first_valid_image['longitude']+' '+first_valid_image['latitude']+')'
        end_position = 'SRID=4326;POINT('+image_data[-1]['longitude']+' '+image_data[-1]['latitude']+')'

        transect_shape = bounding_polygon
        start_time_stamp = first_valid_image['date_time']
        end_time_stamp = image_data[-1]['date_time']

        if deployment_path[-1] == '/':
            short_name = deployment_path.split('/')[-2]
        else:
            short_name = deployment_path.split('/')[-1]

        min_depth = str(depth_array.min())
        max_depth = str(depth_array.max())
        contact_person = operator
        license = 'CC-BY'

        deployment_info = dict(type=type,
                               operator=operator,
                               start_position=start_position,
                               end_position=end_position,
                               transect_shape=transect_shape,
                               start_time_stamp=start_time_stamp,
                               end_time_stamp=end_time_stamp,
                               short_name = short_name,
                               mission_aim=description,
                               min_depth=min_depth,
                               max_depth=max_depth,
                               contact_person=contact_person,
                               descriptive_keywords=keywords,
                               license=license)

    else:
        print "ERROR: Can not open the deployment description file."

    return deployment_info


def read_images_file(deployment_path):
    """read images file and put data into a big structure for manipulation
    """
    image_data = []

    if os.path.isfile(os.path.join(deployment_path, images_filename)):
        with open(os.path.join(deployment_path, images_filename), 'rb') as csvfile:
            images_reader = csv.reader(x.replace('\0', '') for x in csvfile)

            row_index = 2
            #skip the header rows (2)
            images_reader.next()
            images_reader.next()

            for row in images_reader:
                row_index = row_index + 1
                image_data_instance = dict(date_time=row[0],
                                           latitude=row[1],
                                           longitude=row[2],
                                           depth=row[3],
                                           image_name=row[4],
                                           camera_name=row[5],
                                           camera_angle=row[6],
                                           temperature=row[7],
                                           salinity=row[8],
                                           pitch=row[9],
                                           roll=row[10],
                                           yaw=row[11],
                                           altitude=row[12],
                                           depth_uncertainty=row[13])
                image_data.append(image_data_instance)
    else:
        print "ERROR: Could not find images.csv file."

    return image_data


def read_camera_data(image_data):
    """ checks images list for the camera a returns a dict for posting
        Note: will eventually handle the multiple camera case, if we ever see a deployment with such.
    """

    if image_data is None:
        # holy hell, something has gone wrong here
        print 'ERROR: Failed to get image data for camera data.'
        return None

    if image_data['camera_angle'].lower() == 'Downward'.lower():
        angle_value = 0
    elif image_data['camera_angle'].lower() == 'Upward'.lower():
        angle_value = 1
    elif image_data['camera_angle'].lower() == 'Slanting/Oblique'.lower():
        angle_value = 2
    elif image_data['camera_angle'].lower() == 'Horizontal/Seascape'.lower():
        angle_value = 3
    else:
        print 'ERROR: camera angle of', image_data['camera_angle'].lower(), 'was not recognised.'
        return None

    camera_data = dict(name=image_data['camera_name'],
                       angle=str(angle_value))

    return camera_data


def write_campaign(campaign_data):
    """
    Write the campaign data to the DB, and return a key.
    """

    campaign = Campaign(**campaign_data)
    campaign.save()
    authorization.make_campaign_public(campaign)

    return campaign.id


def write_deployment(campaign_key, deployment_data):
    """
    Write the deployment data to the db, and return a key.
    """

    deployment = Deployment(**deployment_data)
    deployment.campaign_id = campaign_key
    deployment.save()

    return deployment.id


def write_measurement(image, type, unit, value):
    measurement = Measurement(image=image, measurement_type=type, measurement_unit=unit, value=value)
    measurement.save()


def write_images(deployment_key, image_data):
    """
    Write the image, measurement and camera data to the db, for the given deployment.
    """

    for image_data_dict in image_data:

        print "------------------>>> " + image_data_dict['longitude']+" "+image_data_dict['latitude']

        #save the image
        image = Image(deployment_id=deployment_key,
                      image_name=image_data_dict['image_name'],
                      date_time=image_data_dict['date_time'],
                      position="SRID=4326;POINT("+image_data_dict['longitude']+" "+image_data_dict['latitude']+")",
                      #depth=image_data_dict['depth'],
                      #depth_uncertainty=image_data_dict['depth_uncertainty'],
                      )
        image.save()

        write_measurement(image, 'depth', 'm', image_data_dict['depth'])
        write_measurement(image, 'depth_uncertainty', 'm', image_data_dict['depth_uncertainty'])
        write_measurement(image, 'temperature', 'cel', image_data_dict['temperature'])
        write_measurement(image, 'salinity', 'psu', image_data_dict['salinity'])
        write_measurement(image, 'pitch', 'rad', image_data_dict['pitch'])
        write_measurement(image, 'roll', 'rad', image_data_dict['roll'])
        write_measurement(image, 'yaw', 'rad', image_data_dict['yaw'])
        write_measurement(image, 'altitude', 'm', image_data_dict['altitude'])

        #link the camera to the image
        camera_data_dict = read_camera_data(image_data_dict)
        camera = Camera(**camera_data_dict)
        camera.image = image
        camera.save()

    return None


def main():
    """
        Main function.
    """

    root_import_path = os.getcwd()

    if not os.path.isdir(root_import_path):
        print 'ERROR: This is not a valid path.'
        sys.exit()

    Campaign.objects.all().delete()
    Deployment.objects.all().delete()

    campaign_data = read_campaign(root_import_path)
    campaign_key = write_campaign(campaign_data)

    directories = [o for o in os.listdir(root_import_path) if os.path.isdir(os.path.join(root_import_path, o)) and not o.startswith('.')]

    for directory in directories:
        image_data = read_images_file(os.path.join(root_import_path, directory))
        deployment_data = read_deployment_file(os.path.join(root_import_path, directory), image_data)

        deployement_key = write_deployment(campaign_key, deployment_data)
        write_images(deployement_key, image_data)


    campaigns = Campaign.objects.all()
    deployments = Deployment.objects.all()
    images = Image.objects.all()

    for campaign in campaigns:
        print campaign

    for deployment in deployments:
        print deployment

    for image in images:
        print image.image_name

    # read and write campaign

    # read and write deployments

    # read and write images for deployments


if __name__ == "__main__":
    main()