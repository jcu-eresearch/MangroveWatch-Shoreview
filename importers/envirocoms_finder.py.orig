import datetime
import time
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import sys
import django
import numpy as np

sys.path.append('/home/benthobox/benthobox')
import os
# Bind to django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "benthobox.settings")

from catamidb import authorization
from catamidb.models import Campaign, Deployment, Measurement, Camera, Image


class EcomsFinder():

    def __init__(self, environcoms_url, organisation_id, collection_type, username, password):
        self.environcoms_url = environcoms_url
        self.organisation_id = organisation_id
        self.collection_type = collection_type
        self.limit = '100'
        self.username = username
        self.password = password
        self.campaigns = []
        self.deployments = []
        #self.images = []
        self.valid_campaign_ids = []
        self.valid_deployment_ids = []
        self.get_mappings()

    def get_url(self, url):
        """
        Handles paginated reponses from the API. Bundles the pages into a single response
        :param url:
        :return:
        """
        cont = True
        ret = []
        offset = 0

        while cont:
            res = requests.get(url, auth=HTTPDigestAuth(self.username, self.password), params={'offset':offset, 'limit': self.limit})

            if res.status_code != 200:
                print "ERROR: Failed to load the url (%s) got code %s" % (url, res.status_code)
                sys.exit()

            res = res.json()
            ret += res['results']

            if res["count"] - res["offset"] < res["limit"]:
                cont = False
            else:
                offset += res["limit"]

        return ret

    def mapping_for(self, string):
        for item in self.mappings:
            if item['name'] == string:
                return item['identifier']

    def get_mappings(self):

        url = self.environcoms_url + "/collectiontypes/%s" % self.collection_type
        response = requests.get(url, auth=HTTPDigestAuth(self.username, self.password))

        if response.status_code == 200:
            self.mappings = response.json()['fields']
        else:
            print "ERROR: Failed to load the mappings (%s)" % response.status_code
            sys.exit()

    def find(self):

        #get campaigns
        self.campaigns = self.find_campaigns()

        for campaign in self.campaigns:

            # get deployments
            campaign['deployments'] = self.find_deployments(campaign)

            for deployment in campaign['deployments']:

                # get images
                deployment['images'] = self.find_images(deployment)

    def find_campaigns(self):
        """
        Campaigns are mapped to projects /organisations/{organisationid}/projects/
        """

        url = self.environcoms_url + "/organisations/%s/projects/" % self.organisation_id
        response = requests.get(url, auth=HTTPDigestAuth(self.username, self.password))

        if response.status_code == 200:
            return response.json()
        else:
            print "ERROR: Failed to load the campaigns %s" % response.status_code
            sys.exit()

    def find_deployments(self, campaign):
        """
        Deployments are mapped to datasets /datasets?project={project_id}
        """

        url = self.environcoms_url + "/datasets?project=%s" % campaign['id']
        response = requests.get(url, auth=HTTPDigestAuth(self.username, self.password))

        if response.status_code == 200:
            return response.json()['results']

        else:
            print "ERROR: Failed to load the deployments, for project id {0} (1)".format(campaign['id'], response.status_code)
            sys.exit()

    def find_images(self, deployment):
        """
        Get the images for the deployment
        """

        #url = self.environcoms_url + "/data?&limit={0}&dataset={1}".format(self.limit, deployment['id'])
        #response = requests.get(url, auth=HTTPDigestAuth(self.username, self.password))

        url = self.environcoms_url + "/data?dataset={0}".format(deployment['id'])
        return self.get_url(url)

        #if response.status_code == 200:
        #    return response.json()['results']

        #else:
        #    print "ERROR: Failed to load the images, for deployment id {0} ({1})".format(deployment['id'], response.status_code)
        #    sys.exit()

    def validate(self):

        # do campaigns have atleast one deployment and one image?
        for campaign in self.campaigns:
            for deployment in campaign['deployments']:
                if len(deployment['images']) > 0 and self.images_valid(deployment['images']):
                    print "Found valid campaigns and deployment with ids - ", campaign['id'], " - ", deployment['id']
                    self.valid_campaign_ids.append(campaign['id'])
                    self.valid_deployment_ids.append(deployment['id'])

    def images_valid(self, images):
        try:
            # just test all the properties can be found on the image JSON
            for image in images:
                image_api_path = '/{0}/{1}/{2}'.format(image['dataset'], image['id'], self.mapping_for('Image'))

                image_name = image['data'][self.mapping_for('Image')]['originalFileName']
                image_data_instance = dict(date_time=image['timestamp'],
                                           latitude=image['data'][self.mapping_for('Latitude')],
                                           longitude=image['data'][self.mapping_for('Longitude')],
                                           depth=image['data'][self.mapping_for('Depth')],
                                           image_name=image_name,
                                           image_path=image_api_path,
                                           camera_name=image['data'][self.mapping_for('Camera')],
                                           camera_angle=image['data'][self.mapping_for('Camera Angle')],
                                           temperature=image['data'][self.mapping_for('Temperature')],
                                           salinity=image['data'][self.mapping_for('Salinity')],
                                           pitch=image['data'][self.mapping_for('Pitch')],
                                           roll=image['data'][self.mapping_for('Roll')],
                                           yaw=image['data'][self.mapping_for('Yaw')],
                                           altitude=image['data'][self.mapping_for('Altitude')],
                                           depth_uncertainty=image['data'][self.mapping_for('Depth Uncertanity')],
                                           image_type='envirocoms')

            # if we get here then all is valid
            return True

        except:
            # if we get here this is invalid
            return False

    def _import(self):

        for campaign in self.campaigns:

            # if valid
            if campaign['id'] in self.valid_campaign_ids:

                print "Importing project, ", campaign['id'], " - ", campaign['title']
                campaign_key = self.write_campaign(campaign)

                for deployment in campaign['deployments']:

                    # if valid
                    if deployment['id'] in self.valid_deployment_ids:
                        print "Importing deployment, ", deployment['id'], " - ", deployment['title']

                        image_data = self.images_to_dicts(deployment['images'])
                        extras = self.calculate_extras(image_data)

                        deployment_key = self.write_deployment(campaign_key, deployment, extras)
                        self.write_images(deployment_key, image_data)

    def write_campaign(self, campaign_data):
        """
        Write the campaign data to the DB, and return a key.
        """

        date_start = datetime.datetime.strptime(campaign_data['startDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
        date_end = datetime.datetime.strptime(campaign_data['endDate'], '%Y-%m-%dT%H:%M:%S.%fZ')

        # check if the campaign already exists
        campaigns = Campaign.objects.filter(date_start=date_start,
                                            short_name=campaign_data['title'])

        if campaigns.count() > 0:
            print "Campaign %s already exists." % campaigns[0].short_name
            return campaigns[0].id

        campaign = Campaign(short_name=campaign_data['title'],
                            date_start=date_start,
                            date_end=date_end,
                            associated_researchers='',
                            associated_publications='',
                            associated_research_grant='',
                            contact_person=campaign_data['primaryContact'])
        campaign.save()
        authorization.make_campaign_public(campaign)

        return campaign.id

    def write_deployment(self, campaign_key, deployment_data, extras):
        """
        Write the deployment data to the db, and return a key.
        """

        start_time_stamp = datetime.datetime.strptime(extras[3], '%Y-%m-%dT%H:%M:%S.%fZ')
        end_time_stamp = datetime.datetime.strptime(extras[4], '%Y-%m-%dT%H:%M:%S.%fZ')

        # check if the deployment already exists
        deployments = Deployment.objects.filter(start_time_stamp=start_time_stamp,
                                                short_name=deployment_data['title'],
                                                )

        if deployments.count() > 0:
            print "Deployment %s already exists." % deployments[0].short_name
            return deployments[0].id

        deployment = Deployment(start_time_stamp=start_time_stamp,
                                end_time_stamp=end_time_stamp,
                                short_name=deployment_data['title'],
                                mission_aim=deployment_data['description'],
                                type="SVAM",
                                operator="",
                                start_position=extras[0],
                                end_position=extras[1],
                                transect_shape=extras[2],
                                min_depth=extras[5],
                                max_depth=extras[6],
                                contact_person="",
                                descriptive_keywords="",
                                license="")
        deployment.campaign_id = campaign_key
        deployment.save()

        return deployment.id

    def write_measurement(self, image, type, unit, value):
        measurement = Measurement(image=image, measurement_type=type, measurement_unit=unit, value=value)
        measurement.save()

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

    def write_images(self, deployment_key, image_data):
        """
        Write the image, measurement and camera data to the db, for the given deployment.
        """

        for image_data_dict in image_data:

            date_time = datetime.datetime.strptime(image_data_dict['date_time'], '%Y-%m-%dT%H:%M:%S.%fZ')

            try:
                #save the image
                image = Image(deployment_id=deployment_key,
                              image_name=image_data_dict['image_name'],
                              image_path=image_data_dict['image_path'],
                              date_time=date_time,
                              position="SRID=4326;POINT("+str(image_data_dict['longitude'])+" "+str(image_data_dict['latitude'])+")",
                              image_type=image_data_dict['image_type']

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

    def images_to_dicts(self, images):

        image_data = []

        for image in images:
            image_api_path = '/{0}/{1}/{2}'.format(image['dataset'], image['id'], self.mapping_for('Image'))
            image_name = image['data'][self.mapping_for('Image')]['originalFileName']

            image_data_instance = dict(date_time=image['timestamp'],
                                       latitude=image['data'][self.mapping_for('Latitude')],
                                       longitude=image['data'][self.mapping_for('Longitude')],
                                       depth=image['data'][self.mapping_for('Depth')],
                                       image_name=image_name,
                                       image_path=image_api_path,
                                       camera_name=image['data'][self.mapping_for('Camera')],
                                       camera_angle=image['data'][self.mapping_for('Camera Angle')],
                                       temperature=image['data'][self.mapping_for('Temperature')],
                                       salinity=image['data'][self.mapping_for('Salinity')],
                                       pitch=image['data'][self.mapping_for('Pitch')],
                                       roll=image['data'][self.mapping_for('Roll')],
                                       yaw=image['data'][self.mapping_for('Yaw')],
                                       altitude=image['data'][self.mapping_for('Altitude')],
                                       depth_uncertainty=image['data'][self.mapping_for('Depth Uncertanity')],
                                       image_type='envirocoms')
            image_data.append(image_data_instance)

        return image_data

    def calculate_extras(self, image_data):

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
        start_position = 'SRID=4326;POINT('+str(first_valid_image['longitude'])+' '+str(first_valid_image['latitude'])+')'
        end_position = 'SRID=4326;POINT('+str(image_data[-1]['longitude'])+' '+str(image_data[-1]['latitude'])+')'

        transect_shape = bounding_polygon
        start_time_stamp = first_valid_image['date_time']
        end_time_stamp = image_data[-1]['date_time']
        min_depth = str(depth_array.min())
        max_depth = str(depth_array.max())

        return start_position, end_position, transect_shape, start_time_stamp, end_time_stamp, min_depth, max_depth

def main():
    """
        Main function.
    """

    environcoms_url = "http://144.6.226.206/ecoms/api/user_v1"
    username = 'tjeu0nvs7r0ck4sm2ndb18d316'
    password = '70m3jrus8gbv56v14jkqv0nvd'
    organisation_id = 8
    collection_type = 1

    if not environcoms_url:
        print 'ERROR: Exiting because no URL specified.'
        sys.exit()

    ecoms_finder = EcomsFinder(environcoms_url, organisation_id, collection_type, username, password)

    print "Locating campaigns, deployments and images."
    ecoms_finder.find()

    print "Validating data..."
    ecoms_finder.validate()

    print "Importing valid data."
    ecoms_finder._import()

if __name__ == "__main__":
    main()