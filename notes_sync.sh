#!/usr/bin/env bash
cd $1
git pull origin master
git add .
git commit -m "synced with notes folder"
git push origin master
