#!/bin/bash

cd /var/www/wordpress
chown -R www-data:www-data wp-content/uploads
source /etc/apache2/envvars
exec apache2 -D FOREGROUND

