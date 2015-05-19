"""
Run this script inside the campaign directory you want to validate the contents for.

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

import os
import os.path
import argparse
import csv
import json
import numpy as np
import time
import sys
from PIL import Image
from datetime import datetime

#Filenames for critical campaign/deployment files
images_filename = 'images.csv'
description_filename = 'description.txt'
campaign_filename = 'campaign.txt'

def check_campaign(root_import_path):
    """
        Check campaign.txt for valid contents.
    """
    #check campaign file
    if os.path.isfile(os.path.join(root_import_path, campaign_filename)):
        # any missing **required** fields will make this false. spawns MISSING error. Fatal.
        is_complete = True

        # any missing data will make this false. spawns a warning.
        is_minally_ok = True

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

        if version.replace(" ", "") != '1.0':
            print 'ERROR: Version must be 1.0'
            is_broken = True

        if len(name.replace(" ", "")) == 0:
            print 'MISSING:', campaign_filename, ': campaign name is required'
            is_complete = False

        if len(description_text.replace(" ", "")) == 0:
            print 'MISSING:', campaign_filename, ': description is required'
            is_complete = False

        if len(assoc_researchers_text.replace(" ", "")) == 0:
            print 'MISSING:', campaign_filename, ': associated researchers is required'
            is_complete = False

        if len(assoc_publications_text.replace(" ", "")) == 0:
            print 'MISSING:', campaign_filename, ': associated publications is required'
            is_complete = False

        if len(assoc_research_grants_text.replace(" ", "")) == 0:
            print 'MISSING:', campaign_filename, ': associated research grants is required'
            is_complete = False

        if len(start_date_text.replace(" ", "")) == 0:
            print 'MISSING:', campaign_filename, ': start date is required'
            is_complete = False

        if len(end_date_text.replace(" ", "")) == 0:
            print 'MISSING:', campaign_filename, ': end date is required'
            is_complete = False

        if len(contact_person_text.replace(" ", "")) == 0:
            print 'MISSING:', campaign_filename, ': contact person is required'
            is_complete = False

        # check that end date is not before start date (TBD)
        # final summary
        if is_complete:
            print 'SUCCESS: Campaign.txt is verified'
            return True
        else:
            print 'FAILED: Campaign.txt is missing required fields. Verification failed. Check earlier messages.'
            return False

        if not is_complete and is_minally_ok:
            print 'SUCCESS: Campaign.txt is missing optional fields. Review earlier messages.'
            return True

        if is_broken:
            print 'FAILED: Campaign.txt appears to have some bad fields. Check earlier messages'
            return False


def read_deployment_file(deployment_path):
    """reads the description.txt file for the specified deployment
    """

    deployment_info = {}
    if os.path.isfile(os.path.join(deployment_path, description_filename)):
        f = open(os.path.join(deployment_path, description_filename))

        for line in f.readlines():
            split_string = line.rstrip().split(':')
            if split_string[0].lower() == 'Version'.lower():
                deployment_info['version'] = split_string[1].strip()
            elif split_string[0].lower() == 'Type'.lower():
                deployment_info['type'] = split_string[1].strip()
            elif split_string[0].lower() == 'Description'.lower():
                deployment_info['description'] = split_string[1]
            elif split_string[0].lower() == 'Operator'.lower():
                deployment_info['operator'] = split_string[1]
            elif split_string[0].lower() == 'Keywords'.lower():
                deployment_info['keywords'] = split_string[1]

    return deployment_info


def check_deployment(deployment_path):
    """Check deployment for valid contents; description.txt, images.csv and the images themselves
    """
    print 'MESSAGE: Checking', deployment_path

    if os.path.isfile(os.path.join(deployment_path, description_filename)):
        type_list = ['AUV', 'BRUV', 'TI', 'DOV', 'TV']

        # any missing **required** fields will make this false. spawns MISSING error. Fatal.
        is_complete = True

        # any missing data will make this false. spawns a warning.
        is_minally_ok = True

        # True if something wierd happens
        is_broken = False  # True if something wierd happens. Fatal

        deployment_info = read_deployment_file(deployment_path)

        if deployment_info['version'].replace(" ", "") != '1.0':
            print 'ERROR: Version must be 1.0'
            is_broken = True
        if len(deployment_info['type'].replace(" ", "")) == 0:
            print 'MISSING:', description_filename, ': deployment type is required'
            is_complete = False
        if len(deployment_info['description'].replace(" ", "")) == 0:
            print 'MISSING:', description_filename, ': deployment description is required'
            is_complete = False

        #check type
        if not deployment_info['type'].upper() in type_list:
            print 'ERROR: Deployment type of', deployment_info['type'], 'is not recognised. Must be one of', type_list
            is_broken = True

        if is_complete:
            print 'SUCCESS:', description_filename, 'is verified'
            return True
        else:
            print 'FAILED:', description_filename, 'is missing required fields. Verification failed. Check earlier messages.'
            return False

        if not is_complete and is_minally_ok:
            print 'SUCCESS:', description_filename, 'is missing optional fields. Review earlier messages.'
            return True

        if is_broken:
            print 'FAILED:', description_filename, 'appears to have some bad fields. Check earlier messages'
            return False
    else:
        print "ERROR: ", deployment_path, " cannot be found in the deployment path."


def check_deployment_images(deployment_path):
    """
    Check deployment imagery for valid list and valid imagery
    """

    print 'MESSAGE: Checking Deployment', images_filename, '...'
    bad_image_count = 0
    good_image_count = 0

    if os.path.isfile(os.path.join(deployment_path, images_filename)):
        with open(os.path.join(deployment_path, images_filename), 'rb') as csvfile:

            #read the CSV file, scanning for null bytes that the csv row parser cannot handle
            images_reader = csv.reader(x.replace('\0', '') for x in csvfile)

            row_index = 2

            #skip the header rows (2)
            images_reader.next()
            images_reader.next()

            # any missing **required** fields will make this false. spawns MISSING error. Fatal.
            is_complete = True

            # True if something wierd happens
            is_broken = False

            for row in images_reader:
                row_index = row_index + 1

                # any missing **required** fields will make this false. spawns MISSING error. Fatal.
                row_is_complete = True

                # any missing data will make this false. spawns a warning.
                row_has_missing = False

                # True if something wierd happens
                row_is_broken = False

                time_string = row[0]
                latitude = row[1]
                longitude = row[2]
                depth = row[3]
                image_name = row[4]
                camera_name = row[5]
                camera_angle = row[6]
                temperature = row[7]
                salinity = row[8]
                pitch = row[9]
                roll = row[10]
                yaw = row[11]
                altitude = row[12]
                depth_uncertainty = row[13]

                #image list validation
                #required
                if not str(time_string):
                    print 'MISSING:', images_filename, 'row:', row_index, 'Time is required'
                    row_has_missing = True
                if not str(latitude):
                    print 'MISSING:', images_filename, 'row:', row_index, 'latitude is required'
                    row_has_missing = True
                if not str(longitude):
                    print 'MISSING:', images_filename, 'row:', row_index, 'longitude is required'
                    row_has_missing = True
                if not str(depth):
                    print 'MISSING:', images_filename, 'row:', row_index, 'depth is required'
                    row_has_missing = True
                if not str(image_name):
                    print 'MISSING:', images_filename, 'row:', row_index, 'image_name is required'
                    row_has_missing = True
                if not str(camera_name):
                    print 'MISSING:', images_filename, 'row:', row_index, 'camera_name is required'
                    row_has_missing = True
                if not str(camera_angle):
                    print 'MISSING:', images_filename, 'row:', row_index, 'camera_angle is required'
                    row_has_missing = True

                #not required
                if not str(salinity):
                    print 'MISSING:', images_filename, 'row:', row_index, 'salinity is missing'
                if not str(pitch):
                    print 'MISSING:', images_filename, 'row:', row_index, 'pitch is missing'
                if not str(roll):
                    print 'MISSING:', images_filename, 'row:', row_index, 'roll is missing'
                if not str(yaw):
                    print 'MISSING:', images_filename, 'row:', row_index, 'yaw is missing'
                if not str(altitude):
                    print 'MISSING:', images_filename, 'row:', row_index, 'altitude is missing'
                if not str(depth_uncertainty):
                    print 'MISSING:', images_filename, 'row:', row_index, 'depth uncertainty is missing'

                # validate the images
                if not (not str(image_name)): # if string is not blank
                    #lets check this image
                    if os.path.isfile(os.path.join(deployment_path, image_name)):
                        try:
                            Image.open(os.path.join(deployment_path, image_name))
                            good_image_count = good_image_count + 1
                        except:
                            bad_image_count = bad_image_count + 1
                            print 'ERROR:', image_name, ' appears to be an invalid image'
                    else:
                        print 'MISSING:', image_name, ' references in images.csv'
                        row_is_complete = False

                # validate the date time is in the correct format
                try:
                    datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    row_is_complete = False
                    print "ERROR: Time string is not in the correct format."

                #let's decide what to do with this row
                if not row_is_complete:
                    is_complete = False

                if row_is_broken:
                    is_broken = True

            if bad_image_count > 0:
                print 'ERROR:', bad_image_count, '(of', good_image_count, ') bad images were found'
                is_broken = True
            else:
                print 'SUCCESS:', good_image_count, ' images checked'

            #did something important break?
            if is_broken:
                return False

            return is_complete
    else:
        print "ERROR: images.csv cannot be found in the deployment directory."


def main():
    """
        Main function.
    """

    root_import_path = os.getcwd()

    if not os.path.isdir(root_import_path):
        print 'ERROR: This is not a valid path.'
        sys.exit()

    # if we are still going then all required files exist. Yay us!
    campaign_status = check_campaign(root_import_path)

    if campaign_status is False:
        sys.exit()

    directories = [o for o in os.listdir(root_import_path) if os.path.isdir(os.path.join(root_import_path, o)) and not o.startswith('.')]

    for directory in directories:
        print "//-------"
        deployment_status = check_deployment(os.path.join(root_import_path, directory))
        deployment_status = check_deployment_images(os.path.join(root_import_path, directory))
        print "//-------"


    print 'FINISH: All checks are done. If there are no errors, then all is valid.'


if __name__ == "__main__":
    main()