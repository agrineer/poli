#!/bin/bash

# remove backup files and __pycache__ before zipping

for dir in */           # '/' indicates a directory
  do 
      dir=${dir%*/}
      echo $dir
      cd $dir

      find -name "*~" -print -delete # backup files
      find -name __pycache__ -prune -execdir rm -rf {} +
      #find -name "__pycache__" -exec rm -r "{}" \; # data byte direectories
      cd ..
done

for dir in */
  do 
    dir=${dir%*/}
    zip -r $dir $dir 
done
