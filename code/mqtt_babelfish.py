import os
import logging
import logging.config
import yaml
import paho.mqtt.client as mqtt


# Load logging config from logging.yaml
def setup_logging(default_path='./conf/logging.yaml',
                  default_level=logging.INFO, 
                  env_key='LOG_CFG'):
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.load(f)
        logging.config.dictConfig(config)
        logging.info("Configured logging from yaml")
    else:
        logging.basicConfig(level=default_level)
        logging.info("Configured logging basic")


# Load config from yaml file
def load_config(path='./conf/config.yaml'):
    config = None
    log = logging.getLogger(__name__)
    if os.path.exists(path):
        log.debug("Loading config from: " + str(path))
        with open(path, 'r') as y:
            config = yaml.load(y)
        log.debug("Config: " + str(config))
    else:
        log.error("Config file not found: " + path)
    return config

# Callback for connection
def on_connect(client, config, flags, rc):
    log = logging.getLogger(__name__)
    log.info("Connected to mqtt server")
    # Subscribe
    for topic in config["subscribe"]:
        log.info("Subscribing to: " + topic)
        client.subscribe(topic)

def on_message(client, config, msg):
    log = logging.getLogger(__name__)
    if type(msg.payload) == type(b'1'):
        payload = msg.payload.decode('UTF-8')
    else:
        payload = msg.payload
    log.info("Received message: " + msg.topic + " " + payload)
    if msg.topic in config["translate_topic"]:
        # We should translate the incoming message
        # Topic
        t = config["translate_topic"][msg.topic]
        # Message
        if payload in config["translate_message"]:
            m = config["translate_message"][payload]
        else:
            m = payload
        # Republish
        log.info("Republishing to: " + t + " " + str(m))
        client.publish(t, m)

def main():
    setup_logging()
    log = logging.getLogger(__name__)
    log.info("Started babelfish...")

    config = load_config()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    if config["tls"]["ca_certs"]:   
        client.tls_set(ca_certs=config["tls"]["ca_certs"])

    if config["mqtt"]["password"]:
        client.username_pw_set(
            config["mqtt"]["username"],
            password = config["mqtt"]["password"]
        )

    # Give the on connect callback access to the config
    # so we can subscribe to configured topics
    client.user_data_set(config)

    client.connect(config["mqtt"]["host"], config["mqtt"]["port"], 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
