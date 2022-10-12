FROM my-hue-lights-venv-prepped
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /opt/app
ADD ./python/ /opt/app

CMD [ "gunicorn", "-b", "0.0.0.0:5000", "app:create_app()" ]