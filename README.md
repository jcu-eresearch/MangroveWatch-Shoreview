# README

Image Annotation System for Shoreline Assessment and Monitoring.
Developed with funding from the ANDS MODC project

## History

Benthox is a fork of the CATAMI code which can be found here - https://github.com/catami/catami

07-Oct-2015 - Updated SSL config for nginx
Changed install/fabfile.py
	updated nginx config to improve security.
	The new config refers to a Diffie-Helman param.
	The command to generate this has not beed added to the fab scripts, although the config now expects this to exist. 

	command: 'openssl dhparam -out /etc/nginx/ssl/dhparam.pem 4096'

