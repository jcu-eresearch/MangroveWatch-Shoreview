import os
from django.contrib.gis.db import models
from benthobox import settings


class CampaignManager(models.GeoManager):
    """Model Manager for Campaign.
    Provides (by inheritance) gis methods and ability
    to get a campaign by natural key.
    """

    def get_by_natural_key(self, year, month, short_name):
        """Get a campaign from its natural key.
        :date_start: the start date of the campaign
        :short_name: the name of the campaign
        :returns: the campaign with the given natural key

        """

        return self.get(
            date_start__year=year,
            date_start__month=month,
            short_name=short_name
        )


class DeploymentManager(models.GeoManager):
    """Model Manager for Deployment.
    Provides (by inheritance) gis methods and ability
    to get a deployment by natural key.
    """

    def get_by_natural_key(self, start_time_stamp, short_name):
        """Method to get object by its natural key.

        :returns: object represented by the natural key

        """
        return self.get(start_time_stamp=start_time_stamp,
                        short_name=short_name)


class ImageUpload(models.Model):
    """
    Model used to upload images to server, and have server generate thumbnails
    Upload path defaults to "images" folder but will change during POST; use specified "deployment" to get Campaign and Deployment names
    e.g. deployment id = 2, look up Deployment short_name = "r20110612_033752_st_helens_01_elephant_rock_deep_repeat"
    and respective Campaign short_name = "Campaign1"
    Upload image goes into: UPLOAD_PATH/r20110612_033752_st_helens_01_elephant_rock_deep_repeat/Campaign1/images/
    Generated thumbnail goes into: UPLOAD_PATH/r20110612_033752_st_helens_01_elephant_rock_deep_repeat/Campaign1/thumbnails/
    UPLOAD_PATH defined in settings.py
    """

    img = models.ImageField(upload_to="images", null=True, blank=True, max_length=255)


class ImageManager(models.GeoManager):
    """ Handles logic functions related to images """

    def random_sample_images(self, images, sample_size):
        """ Randomly sample images from a set """

        #return sample(images, int(sample_size))
        return images.order_by('?')[:sample_size]

    def stratified_sample_images(self, images, sample_size):
        """ Stratified sample images from a set """

        images.order_by('deployment', 'date_time')
        every_nth = images.count()/int(sample_size)
        sampled_images = images[0:images.count():every_nth]

        return sampled_images

    def construct_path_from_deployment(self, deployment, context_path, import_path) :
        """ Using specified deployment id,get Campaign and Deployment ids, which is used to create path for image and thumbnails """
        deploymentId = str(deployment.id)
        campaignId = str(deployment.campaign.id)
        return os.path.join(import_path, campaignId, deploymentId, context_path, "")

    def get_image_destination(self, deployment, import_path) :
        """ Return web location of image """
        return self.construct_path_from_deployment(deployment, "images", import_path)

    def get_thumbnail_destination(self, deployment, import_path) :
        """ Return web location of thumbnail """
        return self.construct_path_from_deployment(deployment, "thumbnails", import_path)

    def get_image_location(self, imageDest, imgName) :
        """ Return absolute location of image """
        return os.path.normpath(imageDest + imgName)

    def get_thumbanail_location(self, thumbDest, imageName, thumbnail_size) :
        """ Return absolute location of thumbnail """
        imgNameNoExt, imgExt = os.path.splitext(imageName)
        size = str(thumbnail_size[0]) + "x" + str(thumbnail_size[1])
        return os.path.normpath(thumbDest + imgNameNoExt + "_" + size + imgExt)

    def get_image_path(self, image):
        #return settings.IMPORT_PATH + "/" + str(image.deployment.campaign.id) + "/" + str(image.deployment.id) + "/images/" + image.image_name
        return settings.IMPORT_PATH + "/" + image.deployment.campaign.short_name + "/" + image.deployment.short_name + "/" + image.image_name

    def get_image_url(self, image, hostname):
        """
        Return the URL for the image
        :param image:
        :return:
        """

        if image.image_type == 'local':
            return "http://" + hostname + "/" + settings.IMAGES_URL + "/" + image.deployment.campaign.short_name + "/" + image.deployment.short_name + "/" + image.image_name
        elif image.image_type == 'envirocoms':
            return "http://" + hostname + "/ecoms_proxy?image=" + image.image_path

    def get_thumbnail_url(self, image_url):
        """
        Return the URL for the thumbnail
        :param image:
        :return:
        """

        return settings.THUMBNAILER_URL + image_url