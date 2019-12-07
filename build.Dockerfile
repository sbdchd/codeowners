FROM quay.io/pypa/manylinux2014_x86_64@sha256:24f1a674af73241de3b0ff14ee7ae5a5af047cc0af2f20c787e8adae92ca249d

ENV PATH /root/.cargo/bin:$PATH
# Add all supported python versions
ENV PATH /opt/python/cp35-cp35m/bin/:/opt/python/cp36-cp36m/bin/:/opt/python/cp37-cp37m/bin/:/opt/python/cp38-cp38/bin/:$PATH
# Otherwise `cargo new` errors
ENV USER root

RUN curl https://www.musl-libc.org/releases/musl-1.1.20.tar.gz -o musl.tar.gz \
    && tar -xzf musl.tar.gz \
    && rm -f musl.tar.gz \
    && cd musl-1.1.20 \
    && ./configure \
    && make install -j2 \
    && cd .. \
    && rm -rf x86_64-unknown-linux-musl \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    && rustup toolchain add nightly-2019-05-04 \
    && rustup target add x86_64-unknown-linux-musl \
    && mkdir /io \
    && python3 -m pip install cffi

RUN python3 -m pip install pyo3-pack==0.7.0-beta.12

WORKDIR /io

ENTRYPOINT ["pyo3-pack"]
