# -*- coding: utf-8 -*-
#
# Copyright © 2013 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import itertools

# TODO: probably should move this to pulp.common

DEFAULT_PAGE_SIZE = 1000


def paginate(iterable, page_size=DEFAULT_PAGE_SIZE):
    # this won't work properly if we give islice something that isn't a generator
    generator = (x for x in iterable)
    while True:
        page = tuple(itertools.islice(generator, 0, page_size))
        if not page:
            return
        yield page