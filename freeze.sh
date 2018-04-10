#!/bin/bash

pip3 freeze | grep pkg-resources > requirements.txt

