#nginx/Dockerfile
FROM nginx:alpine
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY frontend /var/www/html

RUN chmod -R +r /etc/nginx/nginx.conf
RUN chmod -R o+r /var/www/html