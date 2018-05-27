1. Launch AWS Ubuntu 16.04 LTS instance
2. Add HTTP inbound traffic to the security group for the EC2 instance at port 80
3. Run the following commands via SSH

sudo apt-get update && sudo apt-get -y upgrade
sudo apt-get install mysql-server (Set the MySQL root password in this step)
sudo apt-get install libmysqlclient-dev
sudo apt-get install python-pip

cd /home/ec2-user
mkdir myflaskapp
pip install flask
pip install flask-mysqldb
pip install Flask-WTF
pip install passlib
pip install gunicorn

4. Copy the SQL dump file to /home/ubuntu/myflaskapp

5. Setup MySQL

mysql -u root -p < Dump20180525.sql

6. In MySQL prompt type the following

create user 'admin'@'localhost' identified by 'admin';
grant select, insert, update, delete on myflaskapp.* to 'admin'@'localhost';
flush privileges;
exit

7. Setup SQL config and Restart MySQL

cd /etc/mysql
sudo nano my.cnf
<Add the following to the file and save it>
[mysqld]
sql_mode = "STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION"

sudo service mysql restart

8. Copy app.py and the templates folder via WinSCP to /home/ubuntu/myflaskapp

9. Install the Web Server nginx

sudo apt-get install nginx
sudo rm /etc/nginx/sites-enabled/default
sudo nano /etc/nginx/sites-available/myflaskapp

10. Paste the following into the file and save it (Change DNS Name)
server {
    listen       80;
    server_name  ec2-34-224-221-248.compute-1.amazonaws.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}

11. Enable the site, test config, and restart
sudo ln -s /etc/nginx/sites-available/myflaskapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

12. Install supervisor
sudo apt-get install supervisor
cd /etc/supervisor/conf.d
sudo nano myflaskapp.conf

<Add the following to the file and save it>
[program:myflaskapp]
command=/usr/bin/python /home/ubuntu/.local/bin/gunicorn -b localhost:8000 -w 4 app:app
directory=/home/ubuntu/myflaskapp
user=ubuntu
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true

sudo supervisorctl reload
sudo supervisorctl status

13. Test WICApp from any web browser
http://ec2-34-224-221-248.compute-1.amazonaws.com