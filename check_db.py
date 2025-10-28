#!/usr/bin/env python3
import sys
from api.database import check_database_connection

if __name__ == "__main__":
    if check_database_connection():
        sys.exit(0)
    else:
        sys.exit(1)
