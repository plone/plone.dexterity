# -*- coding: utf-8 -*-
import sys

if sys.version_info[0] < 3:  # pragma NO COVER Python2

    PY2 = True
    PY3 = False

    from StringIO import StringIO
    BytesIO = StringIO


else: #pragma NO COVER Python3

    PY2 = False
    PY3 = True

    from io import StringIO
    from io import BytesIO
