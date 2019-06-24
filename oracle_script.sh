data=$1
parsed=$2
alignments=$1.alignments

./alignments.sh $data 

silent="0"
while [[ $# -gt 1 ]]
do
key="$3"
case $key in
    -s|--silent)
    silent="1"
    ;;
    *)
            # unknown option
    ;;
esac
shift # past argument or value
done
if [[ $silent -eq "0" ]];
then
    silent=''
else
    silent='-silent'
fi

python create_data.py -action_type "add" -data $data -parsed $parsed -alignments $alignments $silent
python oracle.py -action_type "add" -data "$parsed.save.p" $silent
python create_data.py -action_type "add_addnode" -data $data -parsed $parsed -alignments $alignments $silent
python oracle.py -action_type "add_addnode" -data "$parsed.save.p" $silent
python create_data.py -action_type "remove" -data $data -parsed $parsed -alignments $alignments $silent
python oracle.py -action_type "remove" -data "$parsed.save.p" $silent
python create_data.py -action_type "remove_rmnode" -data $data -parsed $parsed -alignments $alignments $silent
python oracle.py -action_type "remove_rmnode" -data "$parsed.save.p" $silent
python create_data.py -action_type "merge" -data $data -parsed $parsed -alignments $alignments $silent
python oracle.py -action_type "merge" -data "$parsed.save.p" $silent
python create_data.py -action_type "merge_rmnode" -data $data -parsed $parsed -alignments $alignments $silent
python oracle.py -action_type "merge_rmnode" -data "$parsed.save.p" $silent
python create_data.py -action_type "split" -data $data -parsed $parsed -alignments $alignments $silent
python oracle.py -action_type "split" -data "$parsed.save.p" $silent
python create_data.py -action_type "split_addnode" -data $data -parsed $parsed -alignments $alignments $silent
python oracle.py -action_type "split_addnode" -data "$parsed.save.p" $silent
python create_data.py -action_type "add_sibling" -data $data -parsed $parsed -alignments $alignments $silent
python oracle.py -action_type "add_sibling" -data "$parsed.save.p" $silent
python create_data.py -action_type "add_sibling_addnode" -data $data -parsed $parsed -alignments $alignments $silent
python oracle.py -action_type "add_sibling_addnode" -data "$parsed.save.p" $silent
python create_data.py -action_type "remove_sibling" -data $data -parsed $parsed -alignments $alignments $silent
python oracle.py -action_type "remove_sibling" -data "$parsed.save.p" $silent
python create_data.py -action_type "remove_sibling_rmnode" -data $data -parsed $parsed -alignments $alignments $silent
python oracle.py -action_type "remove_sibling_rmnode" -data "$parsed.save.p" $silent
