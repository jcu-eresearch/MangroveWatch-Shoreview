#!/bin/bash -x
mkdir /home/catami/backups
cd /home/catami/backups
DATE_TIME=$(date +"%d-%m-%y-%H-%M-%s")
echo $DATE_TME
su postgres -c "pg_dump catamidb" > catamidb.${DATE_TIME}.dat.sql
tar -cf catamidb.${DATE_TIME}.tar catamidb.${DATE_TIME}.dat.sql
gzip catamidb.${DATE_TIME}.tar
rm -f catamidb.${DATE_TIME}.dat.sql
