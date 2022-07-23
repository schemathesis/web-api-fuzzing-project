FROM jupyterhub/jupyterhub:1.4.dev

RUN jupyterhub --generate-config

COPY requirements.txt frozen-requirements.txt
RUN pip install --no-cache-dir -r frozen-requirements.txt

ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV WAFP_FUZZER_ID $WAFP_FUZZER_ID
COPY jupyterhub /usr/local/bin/jupyterhub

RUN echo 'root:test' | chpasswd
RUN echo "c.Authenticator.admin_users = {'root'}" >> /srv/jupyterhub/jupyterhub_config.py
RUN echo "c.LocalAuthenticator.create_system_users=True" >> /srv/jupyterhub/jupyterhub_config.py

CMD ["jupyterhub"]
