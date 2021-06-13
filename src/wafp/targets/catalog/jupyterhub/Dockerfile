FROM jupyterhub/jupyterhub:1.4.dev

RUN jupyterhub --generate-config

RUN pip install --upgrade notebook
RUN pip install tornado==6.1.0

# Sentry integration
RUN pip install --upgrade 'sentry-sdk'
ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV WAFP_FUZZER_ID $WAFP_FUZZER_ID
COPY jupyterhub /usr/local/bin/jupyterhub

RUN echo 'root:test' | chpasswd
RUN echo "c.Authenticator.admin_users = {'root'}" >> /srv/jupyterhub/jupyterhub_config.py
RUN echo "c.LocalAuthenticator.create_system_users=True" >> /srv/jupyterhub/jupyterhub_config.py

CMD ["jupyterhub"]
