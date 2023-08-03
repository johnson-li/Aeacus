# cd ~/Workspace/Aeacus
# git submodule update --init --recursive

cd ~/Workspace/Aeacus/submodules/quiche
cargo build --examples --release
cd -
