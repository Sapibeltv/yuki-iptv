# SPDX-License-Identifier: GPL-3.0-only
# pylint: disable=broad-except, too-many-locals, import-error, missing-module-docstring
# pylint: disable=logging-format-interpolation, logging-fstring-interpolation
import os
import gettext
import logging
import requests
from thirdparty.jtv import parse_jtv
from yuki_iptv.xmltv import parse_as_xmltv

_ = gettext.gettext
logger = logging.getLogger(__name__)

def load_epg(epg_url, user_agent):
    '''Load EPG file'''
    logger.info("Loading EPG...")
    logger.info(f"Address: '{epg_url}'")
    if os.path.isfile(epg_url):
        epg_file = open(epg_url, 'rb')
        epg = epg_file.read()
        epg_file.close()
    else:
        epg_req = requests.get(
            epg_url,
            headers={'User-Agent': user_agent},
            stream=True,
            timeout=35
        )
        logger.info(f"EPG URL status code: {epg_req.status_code}")
        epg = epg_req.content
    logger.info("EPG loaded")
    return epg

def merge_two_dicts(dict1, dict2):
    ''' Merge two dictionaries'''
    dict_new = dict1.copy()
    dict_new.update(dict2)
    return dict_new

def fetch_epg(settings, catchup_days1, progress_dict):
    '''Parsing EPG'''
    programmes_epg = {}
    prog_ids = {}
    epg_ok = True
    exc = None
    epg_failures = []
    epg_exceptions = []
    epg_icons = {}
    epg_settings_url = [settings['epg']]
    if ',' in epg_settings_url[0]:
        epg_settings_url[0] = '^^::MULTIPLE::^^' + ':::^^^:::'.join(epg_settings_url[0].split(','))
    if epg_settings_url[0].startswith('^^::MULTIPLE::^^'):
        epg_settings_url = epg_settings_url[0].replace('^^::MULTIPLE::^^', '').split(':::^^^:::')
    epg_i = 0
    for epg_url_1 in epg_settings_url:
        epg_i += 1
        try:

            progress_dict[0] = _('Updating TV guide... (loading {}/{})').format(
                epg_i,
                len(epg_settings_url)
            )

            epg = load_epg(epg_url_1, settings["ua"])

            progress_dict[0] = _('Updating TV guide... (parsing {}/{})').format(
                epg_i,
                len(epg_settings_url)
            )

            try:
                pr_xmltv = parse_as_xmltv(
                    epg, settings, catchup_days1, progress_dict, epg_i, epg_settings_url
                )
                programmes_epg = merge_two_dicts(programmes_epg, pr_xmltv[0])
                prog_ids = merge_two_dicts(prog_ids, pr_xmltv[1])
            except: # pylint: disable=bare-except
                programmes_epg = merge_two_dicts(programmes_epg, parse_jtv(epg, settings))
            try:
                epg_icons = merge_two_dicts(epg_icons, pr_xmltv[2])
            except: # pylint: disable=bare-except
                pass
            epg_failures.append(False)
            logger.info("Parsing done!")
            logger.info("Parsing EPG...")
        except Exception as exc0:
            logger.warning("Failed parsing EPG!")
            epg_failures.append(True)
            epg_exceptions.append(exc0)
    if False not in epg_failures:
        epg_ok = False
        exc = epg_exceptions[0]
    progress_dict[0] = ''
    logger.info("Parsing EPG done!")
    return [{}, programmes_epg, epg_ok, exc, prog_ids, epg_icons]

def worker(procnum, sys_settings, catchup_days1, return_dict1, progress_dict): # pylint: disable=unused-argument
    '''Worker running from multiprocess'''
    epg = fetch_epg(sys_settings, catchup_days1, progress_dict)
    return_dict1[0] = epg[0]
    return_dict1[1] = epg[1]
    return_dict1[2] = True
    return_dict1[3] = epg[2]
    return_dict1[4] = epg[3]
    return_dict1[5] = epg[4]
    return_dict1[6] = epg[5]
    progress_dict[0] = _('Updating TV guide...')