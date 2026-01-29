import boto3
import logging
from hexlogger import HLogger
_logr = HLogger.getLogger(__name__)


def get_landzone_id(_response):
  _logr.info('Getting the landing zone id')
  if not _response:
    _landing_zone = _response['landingZones'][0]
    _lz_id = {_response['LandingZone']['LandingZoneIdentifier']}
    _logr.info(f'Landing Zone ID   : {_lz_id}')
    _logr.info(f"Status            : {_response['LandingZone']['Status']}")
    _logr.info(f"Version           : {_response['LandingZone']['Version']}")
    return _lz_id
  else:
    _logr.info('No landing zone found.');
    return "No landing zone found."


def main() :
  _client = boto3.client('controltower')
  _logr.info("Started")
  get_landzone_id("Hello")
  

if __name__ == "__main__":
  main()