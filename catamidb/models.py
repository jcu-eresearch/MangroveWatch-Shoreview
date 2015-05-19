"""

Data models for the core data storage.

"""
from random import sample
from django.contrib.auth.models import Group

from django.contrib.gis.db import models
from django.dispatch import receiver
from guardian.shortcuts import assign
from userena.signals import signup_complete
import logging
import os
from benthobox import settings
from django.core.validators import MinValueValidator
from catamidb.managers import *

logger = logging.getLogger(__name__)


class Campaign(models.Model):
    """A campaign describes a field campaign that has many deployments."""
    objects = CampaignManager()

    short_name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    associated_researchers = models.TextField()
    associated_publications = models.TextField()
    associated_research_grant = models.TextField()
    date_start = models.DateField()
    date_end = models.DateField()

    contact_person = models.TextField()

    def __unicode__(self):
        return "{0} - {1}".format(self.date_start, self.short_name)

    def natural_key(self):
        """Return the natural key for this Campaign.
        :returns: tuple representing the natural key
        """

        return (self.date_start.year, self.date_start.month, self.short_name)

    class Meta:
        """Defines Metaparameters of the model."""
        unique_together = (('date_start', 'short_name'), )
        permissions = (('view_campaign', 'View the campaign'), )


class Deployment(models.Model):
    """
    Defining a simple Deployment Model. Operator is included in the model as part of denormalising the subtypes
    This is to replace existing Deployment and subtypes BRUVDeployment, DOVDeployment, TIDEDeployment and TVDeployment
    
    """
    objects = DeploymentManager()

    type = models.CharField(max_length=100)
    operator = short_name = models.CharField(max_length=100)

    start_position = models.PointField()
    end_position = models.PointField()
    transect_shape = models.PolygonField()

    start_time_stamp = models.DateTimeField()
    end_time_stamp = models.DateTimeField()

    short_name = models.CharField(max_length=100)
    mission_aim = models.TextField()

    min_depth = models.FloatField()
    max_depth = models.FloatField()

    campaign = models.ForeignKey(Campaign)

    contact_person = models.TextField()
    descriptive_keywords = models.TextField()
    license = models.TextField()

    def __unicode__(self):
        return "Deployment: {0} - {1}".format(
                self.start_time_stamp, self.short_name
            )

    def natural_key(self):
        """Get the natural key of this object.
        :returns: tuple representing the natural key
        """

        return (self.start_time_stamp, self.short_name)

    class Meta:
        """Defines Metaparameters of the model."""
        unique_together = (('start_time_stamp', 'short_name'), )


class Image(models.Model):
    """
    Defining a simple image Model. Depth is included in the model to make
    queries flat, simple and faster.

    This is to replace existing Image and Pose.
    """

    IMAGE_TYPES = (
        ('local', 'local'),
        ('envirocoms', 'envirocoms')
    )

    image_type = models.CharField(max_length=50, choices=IMAGE_TYPES)
    image_path = models.CharField(max_length=200, null=True, blank=True)
    deployment = models.ForeignKey(Deployment)
    image_name = models.CharField(max_length=200)   
    date_time = models.DateTimeField()
    position = models.PointField()

    objects = models.GeoManager()

    #depth = models.FloatField()
    #depth_uncertainty = models.FloatField(null=True, validators=[MinValueValidator(0.0)])

    class Meta:
        """Defines Metaparameters of the model."""
        unique_together = (('date_time', 'deployment'), )


class Measurement(models.Model):

    """

    A generic measurement model, to handle all type of measurements or observations made along side an image.

    """

    MEASUREMENT_TYPES = (
        ('temperature', 'temperature'),
        ('salinity', 'salinity'),
        ('pitch', 'pitch'),
        ('roll', 'roll'),
        ('yaw', 'yaw'),
        ('altitude', 'altitude'),
        ('depth', 'depth'),
        ('depth_uncertainty', 'depth_uncertainty'),
    )

    UNITS_CHOICES = (
        ('ppm', 'ppm'),
        ('ms', 'm s<sup>-1</sup>'),
        ('m', 'm'),
        ('cel', '&ordm;C'),
        ('rad', 'radians'),
        ('deg', '&ordm;'),
        ('psu', 'PSU'),
        ('dbar', 'dbar'),
        ('umoll', 'umol/l'),
        ('umolk', 'umol/kg'),
        ('mgm3', 'mg/m<sup>3</sup>'),
        ('',''),
    )

    image = models.ForeignKey(Image)
    measurement_type = models.CharField(max_length=50, choices=MEASUREMENT_TYPES)
    measurement_unit = models.CharField(max_length=50, choices=UNITS_CHOICES)
    value = models.FloatField()


class Camera(models.Model):
    """Data about a camera used in a deployment.
    Contains information about the orientation and quality of the images
    as well as a name for the camera itself.
    
    This will replace Camera eventually.
    """

    DOWN_ANGLE = 0
    UP_ANGLE = 1
    SLANT_ANGLE = 2
    HORIZONTAL_ANGLE = 3

    CAMERA_ANGLES = (
        (DOWN_ANGLE, 'Downward'),
        (UP_ANGLE, 'Upward'),
        (SLANT_ANGLE, 'Slanting/Oblique'),
        (HORIZONTAL_ANGLE, 'Horizontal/Seascape'),
    )

    image = models.ForeignKey(Image)
    name = models.CharField(max_length=50)
    angle = models.IntegerField(choices=CAMERA_ANGLES)    

    class Meta:
        """Defines Metaparameters of the model."""
        unique_together = (('image', 'name'), )

    '''
class Measurements(models.Model):
    """
    A simple measurements model. To make joins and queries on images
    faster.

    This is to replace ScientificMeasurement models.
    """

    UNITS_CHOICES = (
        ('ppm', 'ppm'),
        ('ms', 'm s<sup>-1</sup>'),
        ('m', 'm'),
        ('cel', '&ordm;C'),
        ('rad', 'radians'),
        ('deg', '&ordm;'),
        ('psu', 'PSU'),
        ('dbar', 'dbar'),
        ('umoll', 'umol/l'),
        ('umolk', 'umol/kg'),
        ('mgm3', 'mg/m<sup>3</sup>'),
        ('',''), 
    )
        
    image = models.ForeignKey(Image)

    #The water temperature at the location (and time) of the image.
    temperature = models.FloatField(null=True, blank=True)
    temperature_unit = models.CharField(max_length=50, choices=UNITS_CHOICES, default='cel')

    #Water salinity at the measurement point.
    salinity = models.FloatField(null=True, blank=True)
    salinity_unit = models.CharField(max_length=50, choices=UNITS_CHOICES, default='psu')

    #Pitch of camera at time of image.
    pitch = models.FloatField(null=True, blank=True)
    pitch_unit = models.CharField(max_length=50, choices=UNITS_CHOICES, default='rad')

    #Roll of camera at time of image.
    roll = models.FloatField(null=True, blank=True)
    roll_unit = models.CharField(max_length=50, choices=UNITS_CHOICES, default='rad')

    #Yaw of camera at time of image.
    yaw = models.FloatField(null=True, blank=True)
    yaw_unit = models.CharField(max_length=50, choices=UNITS_CHOICES, default='rad')

    #Altitude of camera at time of image.
    altitude = models.FloatField(null=True, blank=True)
    altitude_unit = models.CharField(max_length=50, choices=UNITS_CHOICES, default='m')

    '''