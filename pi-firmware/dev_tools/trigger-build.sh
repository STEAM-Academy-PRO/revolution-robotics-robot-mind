# SPDX-License-Identifier: GPL-3.0-only

body='{
"message": "Build triggered by tag $TRAVIS_TAG on RevvyFramework",
"request": {
"branch":"master"
}}'

curl -s -X POST \
   -H "Content-Type: application/json" \
   -H "Accept: application/json" \
   -H "Travis-API-Version: 3" \
   -H "Authorization: token $TRAVIS_API_KEY" \
   -d "$body" \
   https://api.travis-ci.org/repo/RevolutionRobotics%2FBakeRPi/requests