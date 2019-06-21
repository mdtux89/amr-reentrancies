# amr-reentrancies

Scripts for the analysis of reentrancies in AMR discussed in [1].

# Causes of reentrancies

Given an AMR corpus (<amr_file>), follow the instructions to quantify the main causes of reentrancies in your data:

- Preprocess the corpus with the preprocessing scripts of AMREager (https://github.com/mdtux89/amr-eager-multilingual):
  ```
  ./preprocessing.sh -f <amr_file> 
  python preprocessing.py --amrs -f <amr_file>
  ```
  
- Compute the coreferences in the data with ```coref.py```. It requires python3 and neuralcoref (https://github.com/huggingface/neuralcoref):
  ```
  python3 coref.py <amr_file>
  ```

- Run the ```reen_stats.py``` script:
  ```
  python reen_stats.py -prefix <amr_file>
  ```
  
- When using the option ```-verbose``` the script also outputs the examples where one of more reentrancies could not be classified. See [1] for details.


# Oracle experiments

Given an AMR test set (<test_set>) and the output of a parser (<test_set_parsed>):

- To get the results for all actions in isolation:
  ```
  ./oracle_script.sh <test_set> <test_set_parsed>
  ```

- To get the results for the combination of all actions:
  ```
  ./all_actions.sh <test_set> <test_set_parsed>
  ```
  
[1] "The Role of Reentrancies in Abstract Meaning Representation Parsing", Marco Damonte, Ida Szubert, Shay B. Cohen and Mark Steedman. Proceedings of EMNLP (2019). URL: ?
 
