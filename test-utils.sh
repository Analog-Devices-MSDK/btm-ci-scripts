function lower() {
    val=$1
    echo ${val,,}
}

function upper() {
    val=$1
    echo ${val^^}
}
