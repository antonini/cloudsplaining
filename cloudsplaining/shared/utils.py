"""Just some utility functions that don't fit neatly into other categories"""
# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license.
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause
import logging
from hashlib import sha256
from policy_sentry.querying.actions import (
    get_action_data,
    remove_actions_not_matching_access_level,
)
from policy_sentry.querying.all import get_all_service_prefixes

all_service_prefixes = get_all_service_prefixes()
logger = logging.getLogger(__name__)


def remove_wildcard_only_actions(actions_list):
    """Given a list of actions, remove the ones that CANNOT be restricted to ARNs, leaving only the ones that CAN."""
    try:
        actions_list_unique = list(dict.fromkeys(actions_list))
    except TypeError as t_e:  # pragma: no cover
        print(t_e)
        return []
    results = []
    for action in actions_list_unique:
        service_prefix, action_name = action.split(":")
        if service_prefix not in all_service_prefixes:
            continue  # pragma: no cover
        action_data = get_action_data(service_prefix, action_name)

        if len(action_data[service_prefix]) == 0:
            pass  # pragma: no cover
        elif len(action_data[service_prefix]) == 1:
            if action_data[service_prefix][0]["resource_arn_format"] == "*":
                pass
            else:
                # Let's return the CamelCase action name format
                results.append(action_data[service_prefix][0]["action"])
        else:
            results.append(action_data[service_prefix][0]["action"])
    return results


def remove_read_level_actions(actions_list):
    """Given a set of actions, return that list of actions,
    but only with actions at the 'Write', 'Tagging', or 'Permissions management' levels"""
    write_actions = remove_actions_not_matching_access_level(actions_list, "Write")
    permissions_management_actions = remove_actions_not_matching_access_level(
        actions_list, "Permissions management"
    )
    tagging_actions = remove_actions_not_matching_access_level(actions_list, "Tagging")
    modify_actions = tagging_actions + write_actions + permissions_management_actions
    return modify_actions


def get_full_policy_path(arn):
    """
    Resource string will output strings like the following examples.

    Case 1:
      Input: arn:aws:iam::aws:policy/aws-service-role/AmazonGuardDutyServiceRolePolicy
    Output:
      aws-service-role/AmazonGuardDutyServiceRolePolicy
    Case 2:
      Input: arn:aws:iam::123456789012:role/ExampleRole
      Output: ExampleRole
    :param arn:
    :return:
    """
    split_arn = arn.split(":")
    resource_string = ":".join(split_arn[5:])
    resource_string = resource_string.split("/")[1:]
    resource_string = "/".join(resource_string)
    return resource_string


def capitalize_first_character(some_string):
    """Description: Capitalizes the first character of a string"""
    return " ".join("".join([w[0].upper(), w[1:].lower()]) for w in some_string.split())


def get_non_provider_id(name):
    """
    Not all resources have an ID and some services allow the use of "." in names, which breaks our recursion scheme
    if name is used as an ID. Use SHA1(name) instead.
    """
    name_hash = sha256()  # nosec
    name_hash.update(name.encode('utf-8'))
    return name_hash.hexdigest()
