import sys
import django

sys.path.append('/home/benthobox/benthobox')
import os
# Bind to django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "benthobox.settings")

import csv
import fnmatch
from datetime import datetime
import traceback
import numpy as np
from PIL import Image as PILImage
from catamidb import authorization
from catamidb.models import Campaign, Deployment, Measurement, Camera, Image


class LocalFinder():

    def __init__(self, root_import_path):
        self.root_import_path = root_import_path
        self.campaigns = []
        self.deployments = []
        self.images = []
        self.valid_campaigns = {}

    def find(self):

        for root, dirnames, filenames in os.walk(self.root_import_path):

            for filename in fnmatch.filter(filenames, 'campaign.txt'):
                print os.path.join(root, filename)
                self.campaigns.append(os.path.join(root, filename))

            for filename in fnmatch.filter(filenames, 'description.txt'):
                print os.path.join(root, filename)
                self.deployments.append(os.path.join(root, filename))

            for filename in fnmatch.filter(filenames, 'images.csv'):
                print os.path.join(root, filename)
                self.images.append(os.path.join(root, filename))

    def validate(self):

        local_validator = LocalValidator()

        for campaign in self.campaigns:

            # get deployments and images for this campaign
            parent_directory = os.path.dirname(campaign)
            deployments = filter(lambda x: parent_directory in x, self.deployments)
            images = filter(lambda x: parent_directory in x, self.images)

            # is everything valid under this campaign
            valid = local_validator.campaign_deployment_images_valid(campaign, deployments, images)

            self.valid_campaigns[campaign] = valid

    def _import(self):

        local_importer = LocalImporter()

        for campaign in self.campaigns:
            if self.valid_campaigns[campaign] == True:

                #import the campaign
                campaign_key = local_importer.import_campaign(campaign)

                # get deployments and images for this campaign
                parent_directory = os.path.dirname(campaign)
                deployments = filter(lambda x: parent_directory in x, self.deployments)

                #import deployments and images
                for deployment in deployments:
                    parent_directory = os.path.dirname(deployment)
                    images = filter(lambda x: parent_directory in x, self.images)[0]

                    #import deployment and images
                    local_importer.import_deployment_and_images(campaign_key, deployment, images)


class LocalValidator():

    def __init__(self):
        pass

    def campaign_deployment_images_valid(self, campaign_filepath, deployments, images):

        valid = True

        # check the campaign first
        if not self.campaign_valid(campaign_filepath):
            valid = False

        # iterate through the deployments and images, if any are invalid then this campaign is invalid
        for deployment in deployments:
            if not self.deployment_valid(deployment):
                valid = False

        for image in images:
            if not self.images_valid(image):
                valid = False

        return valid

    def campaign_valid(self, campaign_filepath):
        """
            Check campaign.txt for valid contents.
        """

        # check there is a deployment subdirectory
        parent_directory = os.path.dirname(campaign_filepath)

        if len(os.listdir(parent_directory)) == 0:
            print 'FAILED: %s No deployment sub-directory.' % campaign_filepath
            return False

        try:
            #check campaign file
            if os.path.isfile(campaign_filepath):

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

                f = open(campaign_filepath)

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
                    print 'MISSING:', campaign_filepath, ': campaign name is required'
                    is_complete = False

                if len(description_text.replace(" ", "")) == 0:
                    print 'MISSING:', campaign_filepath, ': description is required'
                    is_complete = False

                if len(assoc_researchers_text.replace(" ", "")) == 0:
                    print 'MISSING:', campaign_filepath, ': associated researchers is required'
                    is_complete = False

                if len(assoc_publications_text.replace(" ", "")) == 0:
                    print 'MISSING:', campaign_filepath, ': associated publications is required'
                    is_complete = False

                if len(assoc_research_grants_text.replace(" ", "")) == 0:
                    print 'MISSING:', campaign_filepath, ': associated research grants is required'
                    is_complete = False

                if len(start_date_text.replace(" ", "")) == 0:
                    print 'MISSING:', campaign_filepath, ': start date is required'
                    is_complete = False

                if len(end_date_text.replace(" ", "")) == 0:
                    print 'MISSING:', campaign_filepath, ': end date is required'
                    is_complete = False

                if len(contact_person_text.replace(" ", "")) == 0:
                    print 'MISSING:', campaign_filepath, ': contact person is required'
                    is_complete = False

                # check that end date is not before start date (TBD)
                # final summary
                if is_complete:
                    print 'SUCCESS: %s is valid' % campaign_filepath
                    return True

                if not is_complete and is_minally_ok:
                    print 'SUCCESS: %s is missing optional fields. Review earlier messages.' % campaign_filepath
                    return True

                if is_broken:
                    print 'FAILED: %s appears to have some bad fields. Check earlier messages' % campaign_filepath
                    return False

                else:
                    print 'FAILED: %s is missing required fields. Verification failed. Check earlier messages.' % campaign_filepath
                    return False

            else:
                print 'FAILED: %s not a file.' % campaign_filepath
                return False

        except Exception:
            print 'EXCEPTION: %s ' % campaign_filepath
            traceback.print_exc(file=sys.stdout)
            return False

    def deployment_valid(self, deployment_filepath):
        """
            Check deployment for valid contents; description.txt
        """

        print 'MESSAGE: Checking', deployment_filepath

        try:
            if os.path.isfile(deployment_filepath):
                type_list = ['AUV', 'BRUV', 'TI', 'DOV', 'TV']

                # any missing **required** fields will make this false. spawns MISSING error. Fatal.
                is_complete = True

                # any missing data will make this false. spawns a warning.
                is_minally_ok = True

                # True if something wierd happens
                is_broken = False  # True if something wierd happens. Fatal

                deployment_info = {}
                f = open(deployment_filepath)

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

                if deployment_info['version'].replace(" ", "") != '1.0':
                    print 'ERROR: Version must be 1.0'
                    is_broken = True
                if len(deployment_info['type'].replace(" ", "")) == 0:
                    print 'MISSING:', deployment_filepath, ': deployment type is required'
                    is_complete = False
                if len(deployment_info['description'].replace(" ", "")) == 0:
                    print 'MISSING:', deployment_filepath, ': deployment description is required'
                    is_complete = False

                #check type
                if not deployment_info['type'].upper() in type_list:
                    print 'ERROR: Deployment type of', deployment_info['type'], 'is not recognised. Must be one of', type_list
                    is_broken = True

                if is_complete:
                    print 'SUCCESS:', deployment_filepath, 'is verified'
                    return True

                if not is_complete and is_minally_ok:
                    print 'SUCCESS:', deployment_filepath, 'is missing optional fields. Review earlier messages.'
                    return True

                if is_broken:
                    print 'FAILED:', deployment_filepath, 'appears to have some bad fields. Check earlier messages'
                    return False

                else:
                    print 'FAILED:', deployment_filepath, 'is missing required fields. Verification failed. Check earlier messages.'
                    return False

            else:
                print "ERROR: ", deployment_filepath, " cannot be found in the deployment path."

        except Exception:
            print 'EXCEPTION: %s ' % deployment_filepath
            traceback.print_exc(file=sys.stdout)
            return False

    def images_valid(self, images_filepath):
        """
        Check deployment imagery for valid list and valid imagery
        """

        print 'MESSAGE: Checking images', images_filepath, '...'
        bad_image_count = 0
        good_image_count = 0

        try:
            if os.path.isfile(images_filepath):
                with open(images_filepath, 'rb') as csvfile:

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
                            print 'MISSING:', images_filepath, 'row:', row_index, 'Time is required'
                            row_has_missing = True
                        if not str(latitude):
                            print 'MISSING:', images_filepath, 'row:', row_index, 'latitude is required'
                            row_has_missing = True
                        if not str(longitude):
                            print 'MISSING:', images_filepath, 'row:', row_index, 'longitude is required'
                            row_has_missing = True
                        if not str(depth):
                            print 'MISSING:', images_filepath, 'row:', row_index, 'depth is required'
                            row_has_missing = True
                        if not str(image_name):
                            print 'MISSING:', images_filepath, 'row:', row_index, 'image_name is required'
                            row_has_missing = True
                        if not str(camera_name):
                            print 'MISSING:', images_filepath, 'row:', row_index, 'camera_name is required'
                            row_has_missing = True
                        if not str(camera_angle):
                            print 'MISSING:', images_filepath, 'row:', row_index, 'camera_angle is required'
                            row_has_missing = True

                        #not required
                        if not str(salinity):
                            print 'MISSING:', images_filepath, 'row:', row_index, 'salinity is missing'
                        if not str(pitch):
                            print 'MISSING:', images_filepath, 'row:', row_index, 'pitch is missing'
                        if not str(roll):
                            print 'MISSING:', images_filepath, 'row:', row_index, 'roll is missing'
                        if not str(yaw):
                            print 'MISSING:', images_filepath, 'row:', row_index, 'yaw is missing'
                        if not str(altitude):
                            print 'MISSING:', images_filepath, 'row:', row_index, 'altitude is missing'
                        if not str(depth_uncertainty):
                            print 'MISSING:', images_filepath, 'row:', row_index, 'depth uncertainty is missing'

                        # get imeages path
                        images_path = os.path.dirname(images_filepath)

                        # validate the images
                        if not (not str(image_name)): # if string is not blank
                            #lets check this image
                            if os.path.isfile(os.path.join(images_path, image_name)):
                                try:
                                    PILImage.open(os.path.join(images_path, image_name))
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
                print "ERROR: %s cannot be found in the deployment directory." % images_filepath

        except Exception:
            print 'EXCEPTION: %s ' % images_filepath
            traceback.print_exc(file=sys.stdout)
            return False


class LocalImporter():

    def __init__(self):
        pass

    def import_campaign(self, campaign_file_path):
        campaign_data = self.read_campaign(campaign_file_path)
        campaign_key = self.write_campaign(campaign_data)

        return campaign_key

    def import_deployment_and_images(self, campaign_key, deployment_file_path, images_file_path):
        image_data = self.read_images_file(images_file_path)
        deployment_data = self.read_deployment_file(deployment_file_path, image_data)

        deployement_key = self.write_deployment(campaign_key, deployment_data)
        self.write_images(deployement_key, image_data)

    def read_campaign(self, campaign_file_path):
        """
            Reads campaign.txt and returns contents in a dict
        """

        if os.path.isfile(campaign_file_path):

            version = ''
            name = ''
            description_text = ''
            assoc_researchers_text = ''
            assoc_publications_text = ''
            assoc_research_grants_text = ''
            start_date_text = ''
            end_date_text = ''
            contact_person_text = ''

            f = open(campaign_file_path)

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

    def read_deployment_file(self, deployment_filepath, image_data):
        """
            Reads the description.txt file for the specified deployment
        """

        deployment_info = {}
        if os.path.isfile(deployment_filepath):
            f = open(deployment_filepath)

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

            deployment_filepath_parent = os.path.dirname(deployment_filepath)
            if deployment_filepath[-1] == '/':
                short_name = deployment_filepath_parent.split('/')[-2]
            else:
                short_name = deployment_filepath_parent.split('/')[-1]

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

    def read_images_file(self, images_filepath):
        """read images file and put data into a big structure for manipulation
        """
        image_data = []

        if os.path.isfile(images_filepath):
            with open(images_filepath, 'rb') as csvfile:
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

    def read_camera_data(self, image_data):
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

    def write_campaign(self, campaign_data):
        """
        Write the campaign data to the DB, and return a key.
        """

        # check if the campaign already exists
        campaigns = Campaign.objects.filter(date_start=campaign_data['date_start'], short_name=campaign_data['short_name'])

        if campaigns.count() > 0:
            print "Campaign %s already exists." % campaigns[0].short_name
            return campaigns[0].id

        campaign = Campaign(**campaign_data)
        campaign.save()
        authorization.make_campaign_public(campaign)

        return campaign.id

    def write_deployment(self, campaign_key, deployment_data):
        """
        Write the deployment data to the db, and return a key.
        """

        # check if the deployment already exists
        deployments = Deployment.objects.filter(start_time_stamp=deployment_data['start_time_stamp'], short_name=deployment_data['short_name'])

        if deployments.count() > 0:
            print "Deployment %s already exists." % deployments[0].short_name
            return deployments[0].id

        deployment = Deployment(**deployment_data)
        deployment.campaign_id = campaign_key
        deployment.save()

        return deployment.id

    def write_measurement(self, image, type, unit, value):
        measurement = Measurement(image=image, measurement_type=type, measurement_unit=unit, value=value)
        measurement.save()

    def write_images(self, deployment_key, image_data):
        """
        Write the image, measurement and camera data to the db, for the given deployment.
        """

        for image_data_dict in image_data:

            print "------------------>>> " + image_data_dict['longitude']+" "+image_data_dict['latitude']

            try:
                #save the image
                image = Image(deployment_id=deployment_key,
                              image_name=image_data_dict['image_name'],
                              date_time=image_data_dict['date_time'],
                              position="SRID=4326;POINT("+image_data_dict['longitude']+" "+image_data_dict['latitude']+")",
                              #depth=image_data_dict['depth'],
                              #depth_uncertainty=image_data_dict['depth_uncertainty'],
                              )
                image.save()

                self.write_measurement(image, 'depth', 'm', image_data_dict['depth'])
                self.write_measurement(image, 'depth_uncertainty', 'm', image_data_dict['depth_uncertainty'])
                self.write_measurement(image, 'temperature', 'cel', image_data_dict['temperature'])
                self.write_measurement(image, 'salinity', 'psu', image_data_dict['salinity'])
                self.write_measurement(image, 'pitch', 'rad', image_data_dict['pitch'])
                self.write_measurement(image, 'roll', 'rad', image_data_dict['roll'])
                self.write_measurement(image, 'yaw', 'rad', image_data_dict['yaw'])
                self.write_measurement(image, 'altitude', 'm', image_data_dict['altitude'])

                #link the camera to the image
                camera_data_dict = self.read_camera_data(image_data_dict)
                camera = Camera(**camera_data_dict)
                camera.image = image
                camera.save()

            except django.db.utils.IntegrityError:
                print "Skipping %s, it already exists." % image_data_dict['image_name']

        return None


def main():
    """
        Main function.
    """

    root_import_path = sys.argv[1]

    print root_import_path

    if not os.path.isdir(root_import_path):
        print 'ERROR: This is not a valid path.'
        sys.exit()

    local_finder = LocalFinder(root_import_path)
    local_finder.find()
    local_finder.validate()
    local_finder._import()

if __name__ == "__main__":
    main()