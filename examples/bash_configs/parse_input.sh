# GET_CONFIGS_READY FOR BASH FILE!
POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -exp_dir|--experiment_dir)
    EXPERIMENT_DIR="$2"
    shift # past argument
    shift # past value
    ;;
    -config|--config_fname)
    CONFIG_FNAME="$2"
    shift # past argument
    shift # past value
    ;;
    -seed|--seed_id)
    SEED_ID="$2"
    shift # past argument
    shift # past value
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

mkdir -p ${EXPERIMENT_DIR}
FNAME_WO_EXT="${CONFIG_FNAME##*/}"
FNAME_WO_EXT="${FNAME_WO_EXT%%.*}"
echo "some data for the file" >> "${EXPERIMENT_DIR}/${FNAME_WO_EXT}_${SEED_ID}.txt"
