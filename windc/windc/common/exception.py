# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Glance exception subclasses"""

import urlparse


class RedirectException(Exception):
    def __init__(self, url):
        self.url = urlparse.urlparse(url)


class GlanceException(Exception):
    """
    Base Glance Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.
    """
    message = "An unknown exception occurred"

    def __init__(self, *args, **kwargs):
        try:
            self._error_string = self.message % kwargs
        except Exception:
            # at least get the core message out if something happened
            self._error_string = self.message
        if len(args) > 0:
            # If there is a non-kwarg parameter, assume it's the error
            # message or reason description and tack it on to the end
            # of the exception message
            # Convert all arguments into their string representations...
            args = ["%s" % arg for arg in args]
            self._error_string = (self._error_string +
                                  "\nDetails: %s" % '\n'.join(args))

    def __str__(self):
        return self._error_string


class MissingArgumentError(GlanceException):
    message = "Missing required argument."


class MissingCredentialError(GlanceException):
    message = "Missing required credential: %(required)s"


class BadAuthStrategy(GlanceException):
    message = "Incorrect auth strategy, expected \"%(expected)s\" but "


class NotFound(GlanceException):
    message = "An object with the specified identifier was not found."


class UnknownScheme(GlanceException):
    message = "Unknown scheme '%(scheme)s' found in URI"


class BadStoreUri(GlanceException):
    message = "The Store URI %(uri)s was malformed. Reason: %(reason)s"


class Duplicate(GlanceException):
    message = "An object with the same identifier already exists."


class StorageFull(GlanceException):
    message = "There is not enough disk space on the image storage media."


class StorageWriteDenied(GlanceException):
    message = "Permission to write image storage media denied."


class ImportFailure(GlanceException):
    message = "Failed to import requested object/class: '%(import_str)s'. \
    Reason: %(reason)s"


class AuthBadRequest(GlanceException):
    message = "Connect error/bad request to Auth service at URL %(url)s."


class AuthUrlNotFound(GlanceException):
    message = "Auth service at URL %(url)s not found."


class AuthorizationFailure(GlanceException):
    message = "Authorization failed."


class NotAuthorized(GlanceException):
    message = "You are not authorized to complete this action."


class NotAuthorizedPublicImage(NotAuthorized):
    message = "You are not authorized to complete this action."


class Invalid(GlanceException):
    message = "Data supplied was not valid."


class AuthorizationRedirect(GlanceException):
    message = "Redirecting to %(uri)s for authorization."


class DatabaseMigrationError(GlanceException):
    message = "There was an error migrating the database."


class ClientConnectionError(GlanceException):
    message = "There was an error connecting to a server"


class ClientConfigurationError(GlanceException):
    message = "There was an error configuring the client."


class MultipleChoices(GlanceException):
    message = "The request returned a 302 Multiple Choices. This generally "


class InvalidContentType(GlanceException):
    message = "Invalid content type %(content_type)s"


class BadRegistryConnectionConfiguration(GlanceException):
    message = "Registry was not configured correctly on API server. "


class BadStoreConfiguration(GlanceException):
    message = "Store %(store_name)s could not be configured correctly. "


class BadDriverConfiguration(GlanceException):
    message = "Driver %(driver_name)s could not be configured correctly. "


class StoreDeleteNotSupported(GlanceException):
    message = "Deleting images from this store is not supported."


class StoreAddDisabled(GlanceException):
    message = "Configuration for store failed. Adding images to this "


class InvalidNotifierStrategy(GlanceException):
    message = "'%(strategy)s' is not an available notifier strategy."


class MaxRedirectsExceeded(GlanceException):
    message = "Maximum redirects (%(redirects)s) was exceeded."


class InvalidRedirect(GlanceException):
    message = "Received invalid HTTP redirect."


class NoServiceEndpoint(GlanceException):
    message = "Response from Keystone does not contain a Glance endpoint."


class RegionAmbiguity(GlanceException):
    message = "Multiple 'image' service matches for region %(region)s. This "
