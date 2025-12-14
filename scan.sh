for i in {1..254}; do
    host 192.168.1.$i | grep -v "not found"
done

