#!/bin/bash

pip3 freeze | grep -v pkg-resources > requirements.txt

