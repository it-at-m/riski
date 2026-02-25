# Usecase

The Backend has issues holding db connections if it is not used for a longer period.
This leads to Errors when users access the app after a longer time and therefore get no results unless they trigger the request 3 times.

This script is calling the backend every 30 minutes to keep the connections healthy and enable the users to always get results.