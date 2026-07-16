import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Always return JSON for API errors (including unexpected 500s) so the
    frontend never has to render Django's HTML error page.
    """
    response = exception_handler(exc, context)
    if response is not None:
        return response

    logger.exception('Unhandled API exception in %s', context.get('view'))
    return Response(
        {
            'error': 'Internal server error',
            'detail': str(exc),
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
