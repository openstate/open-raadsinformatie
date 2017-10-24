# This file is used to store password secrets which are not to be committed
# to git. The key has to match one of the sources in the ocd_backend/sources
# directory. If there a secret is required but not supplied in this file, the
# program will fail. A secret like gegevensmagazijn will also match postfixes
# like gegevensmagazijn-moties. The most specific secret is used, so secrets
# like gegevensmagazijn-a will match gegevensmagazijn-a-moties.
#
# Example:
# SECRETS = {
#   'gegevensmagazijn': (
#       "some_user",
#       "some_password",
#   ),
#   'gegevensmagazijn-a': (
#       "some_user",
#       "some_password",
#   ),
# }

SECRETS = {
    '<ID>': (
        "<USERNAME>",
        "<PASSWORD>",
    ),
}
