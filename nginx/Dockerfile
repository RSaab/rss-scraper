FROM nginx:1.19.0-alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx-selfsigned.crt /etc/ssl/certs/
COPY nginx-selfsigned.key /etc/ssl/private/
COPY dhparam.pem /etc/ssl/certs/

COPY self-signed.conf /etc/nginx/conf.d
COPY ssl-params.conf /etc/nginx/conf.d

COPY nginx.conf /etc/nginx/conf.d
