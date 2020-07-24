import logging
import json
import os

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.dispatch_components import AbstractResponseInterceptor
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_core.exceptions import AskSdkException
import ask_sdk_core.utils as ask_utils
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model.interfaces.audioplayer import (
    PlayDirective, PlayBehavior, AudioItem, Stream,
    StopDirective)

logger = logging.getLogger()
logger.setLevel(20)

# Read available radio stations and construct help message
with open('radio_stations.json', 'r') as f:
    RADIO_STATIONS = json.load(f)

stations_string = ''
radio_keys = RADIO_STATIONS.keys()

for key in radio_keys:
    if key == list(radio_keys)[-1]:
        stations_string += 'or ' + key
    else:
        stations_string += key + ', '


WELCOME_MESSAGE = "Welcome to pirate radio. " \
    "Choose radio station"

HELP_MESSAGE = "You can play {}. " \
    "Just say. Play. And the station you'd like to listen to.".format(
        stations_string)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for skill launch with no intent"""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In LaunchRequestHandler")
        response_builder = handler_input.response_builder

        return (
            response_builder
            .speak(WELCOME_MESSAGE)  # the spoken output to the user
            # add a reprompt if you want to keep the session open for the user to respond; only one reprompt allowed
            .ask(HELP_MESSAGE)
            .response
        )


class RadioPlayIntentHandler(AbstractRequestHandler):
    """Handler for Radio Play Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("RadioPlayIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In RadioPlayIntentHandler")

        # Always determining the station from one of the station slot synonyms, since Alexa sucks at catvhing Swedish words.
        station = handler_input.request_envelope.request.intent.slots[
            'station'].resolutions.resolutions_per_authority[0].values[0].value.name

        logger.info("station: {}".format(station))

        speech_text = "{}".format(station)

        directive = PlayDirective(
            play_behavior=PlayBehavior.REPLACE_ALL,
            audio_item=AudioItem(
                stream=Stream(
                    token='this-is-the-audio-token',
                    url=RADIO_STATIONS[station.lower()],
                    offset_in_milliseconds=0
                )
            )
        )

        handler_input.response_builder.speak(speech_text).add_directive(
            directive).set_should_end_session(True)
        return handler_input.response_builder.response


class AudioStopIntentHandler(AbstractRequestHandler):
    """Handler for Stop intent"""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input) or
                is_intent_name("AMAZON.PauseIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Goodbye"

        directive = StopDirective()

        handler_input.response_builder.speak(speech_text).add_directive(
            directive).set_should_end_session(True)
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent"""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        return (
            handler_input.response_builder
            .speak(HELP_MESSAGE)
            .ask(HELP_MESSAGE)
            .response
        )


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent"""

    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")

        speech = (
            "Sorry. I cannot help with that."
        )
        reprompt = "What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(
            reprompt).response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # Any cleanup logic goes here.
        logger.info("In SessionEndedRequestHandler")

        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors."""

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.info("In CatchAllExceptionHandler")
        logger.info("Intent: {}".format(
            handler_input.request_envelope.request))

        logger.error(exception, exc_info=True)
        # logger(handler_input)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )


class LoggingResponseInterceptor(AbstractResponseInterceptor):
    """Invoked immediately after execution of the request handler for an incoming request. 
    Used to print response for logging purposes
    """

    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.debug(
            "Response logged by LoggingResponseInterceptor: {}".format(response))


class LoggingRequestInterceptor(AbstractRequestInterceptor):
    """Invoked immediately before execution of the request handler for an incoming request. 
    Used to print request for logging purposes
    """

    def process(self, handler_input):
        logger.debug("Request received by LoggingRequestInterceptor: {}".format(
            handler_input.request_envelope))

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


# Skill Builder object
sb = CustomSkillBuilder(api_client=DefaultApiClient())

# Add all request handlers to the skill.
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(AudioStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(RadioPlayIntentHandler())
sb.add_request_handler(AudioStopIntentHandler())


# Add exception handler to the skill.
sb.add_exception_handler(CatchAllExceptionHandler())

# Add request and response interceptors
sb.add_global_response_interceptor(LoggingResponseInterceptor())
sb.add_global_request_interceptor(LoggingRequestInterceptor())

# Expose the lambda handler function that can be tagged to AWS Lambda handler
handler = sb.lambda_handler()
