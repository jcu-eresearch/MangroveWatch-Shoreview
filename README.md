# MangroveWatch Shoreview


Image Annotation System for Shoreline Assessment and Monitoring.

Developed with funding from the ANDS MODC project

## Hosts

### Staging

* Nectar VM
* Centos 6

		ec2-user@118.138.241.54

### Production

	http://rdsi-mangrove.hpc.jcu.edu.au/


## Deployment

￼Clone the repo

		git clone https://github.com/jcu-eresearch/MangroveWatch-Shoreview.git​

Install requirements

	cd ​benthobox
	pip install ­-r requirements.txt
	cd ​install

Use fabric to deploy to remote

	fab ­H ​{​host​}​:​{​port​} -​­u {​u​sername​} -​­p ​{p​assword}​ deploy:​{​benthobox_username​}​,​{​benthobox_password​}​,​{​hostname​}​,​{​git_re po​}​,​{​ca_cert_location_on_server​}​,​{​ca_key_location_on_server​}


￼￼￼￼￼￼Once the deployment process has completed you can start the services:

	￼fab ­H ​{​host​}​:​{​port​} -​­u ​{​username​} -​­p ​{​password​}​ start_gunicorn

	fab ­H ​{​host​}​:​{​port​}​­ -u ​{​username​} -​­p ​{​password​}​ start_geoserver

	fab ­H ​{​host​}​:​{​port​} -​­u ​{​username​}​­ -p ​{​password​} ​start_thumbor

	fab ­H ​{​host​}​:​{​port​} -​­u ​{​username​}​­ -p ​{​password​} ​start_nginx

## Development

### Requirements

* python
* pip
* virtualenv

### Installing

Clone the repo

	git clone https://github.com/jcu-eresearch/MangroveWatch-Shoreview.git

Make a virtualenv

	cd MangroveWatch-Shoreview
	virtualenv shoreview


------
**If using Fish shell use virtualfish : **

* https://github.com/adambrenecki/virtualfish/
* https://virtualfish.readthedocs.org/en/latest/usage.html#commands


	vf new shoreview
	vf activate shoreview

or with plugins activated

	mkvirtualenv shoreview
	workon shoreview


-----

**Otherwise using bash-compliant : **

Activate the virtualenv

	source shoreview/bin/activate

Install libraries from `requirements.txt`

	pip install -r requirements.txt



## History
Benthox is a fork of the CATAMI code which can be found here - https://github.com/catami/catami

Benthox is an extension of the original software for use in the shoreline assessment of Mangroves.
