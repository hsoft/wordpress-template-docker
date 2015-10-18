from dockermap.api import DockerClientWrapper, DockerFile, ContainerMap, MappingDockerClient
from dockermap.shortcuts import chmod

#--- Config
PROJECT_NAME = 'myproj'
WORDPRESS_DL_URL = 'https://wordpress.org/wordpress-{}.zip'
WORDPRESS_VERSION = '4.3.1'
WORDPRESS_MD5 = '00508b83cabc79c7d890ad9a905a989b'
DBNAME = PROJECT_NAME
DBUSER = 'root'
DBPASS = 'whatever' # The DB container is never publicly exposed, so this password isn't really sensitive.
WORDPRESS_IMGNAME = '{}-wordpress'.format(PROJECT_NAME)
MARIADB_IMGNAME = '{}-mariadb'.format(PROJECT_NAME)

#--- Private
def _get_client():
    return DockerClientWrapper('unix://var/run/docker.sock')

def _make_worpress():
    APT_DEPS = [
        'curl',
        'zip',
        'apache2',
        'libapache2-mod-php5',
        'php5-mysql',
        'php5-gd',
        'php5-curl',
        'mysql-client',
        'gettext',
    ]
    wpurl = WORDPRESS_DL_URL.format(WORDPRESS_VERSION)
    wpcontent = '/var/www/wordpress/wp-content'
    with DockerFile('ubuntu:trusty') as df:
        df.volumes = ['{}/uploads'.format(wpcontent)]
        df.expose = '80'
        df.command = '/run.sh'
        # Download and install
        df.run(' && '.join([
            'apt-get update',
            'DEBIAN_FRONTEND=noninteractive apt-get -yq install %s' % ' '.join(APT_DEPS),
            'rm -rf /var/lib/apt/lists/*',
        ]))
        df.run(' && '.join([
            'curl -o wordpress.zip -SL {}'.format(wpurl),
            'echo "{} *wordpress.zip" | md5sum -c -'.format(WORDPRESS_MD5),
            'unzip wordpress.zip -d /var/www',
            'rm wordpress.zip',
            'chown -R www-data:www-data /var/www/wordpress',
        ]))
        df.run('cd / && curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar')
        # setup DB
        df.run(' && '.join([
            'cd /var/www/wordpress',
            'php /wp-cli.phar --allow-root core config --dbhost=mariadb --dbname={} --dbuser={} --dbpass={} --skip-check'.format(DBNAME, DBUSER, DBPASS),
        ]))
        # remove useless stuff from WP
        df.run('rm {}/plugins/hello.php'.format(wpcontent))
        # WP/apache config
        df.run('a2enmod rewrite')
        df.add_file('conf/wordpress_apache.conf', '/etc/apache2/sites-enabled/000-default.conf')
        df.add_file('conf/wordpress_run.sh', '/run.sh')
        df.run(chmod('+x', '/run.sh'))
        _get_client().build_from_file(df, WORDPRESS_IMGNAME)

def _make_mariadb():
    with DockerFile('mariadb') as df:
        df.prefix('ENV', 'MYSQL_ROOT_PASSWORD', DBPASS)
        df.prefix('ENV', 'MYSQL_DATABASE', DBNAME)
        _get_client().build_from_file(df, MARIADB_IMGNAME)

def _get_container_map():
    return ContainerMap(PROJECT_NAME, {
        'wordpress': {
            'image': WORDPRESS_IMGNAME,
            'links': 'mariadb',
            'exposes': {80: 80},
        },
        'mariadb': {
            'image': MARIADB_IMGNAME,
        },
    })

#--- Public
def make(target=None, nocache=False):
    print("Building Wordpress image")
    _make_worpress()
    print("Building Database image")
    _make_mariadb()
    print("Done!")

def start(port):
    cmap = _get_container_map()
    print("Starting website on http://localhost:80")
    MappingDockerClient(cmap, _get_client()).startup('wordpress')
    print("Done!")

def stop(clean=False):
    cmap = _get_container_map()
    mapclient = MappingDockerClient(cmap, _get_client())
    print("Stopping instances...")
    for container in ['wordpress', 'mariadb']:
        mapclient.stop(container)
    for container in ['wordpress']:
        mapclient.remove(container)
    if clean:
        print("Cleaning instances...")
        for container in ['mariadb']:
            mapclient.remove(container)
    print("Done!")
