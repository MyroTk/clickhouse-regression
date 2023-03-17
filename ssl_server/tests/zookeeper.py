from testflows.core import *

from ssl_server.tests.common import *
from ssl_server.tests.ssl_context import enable_ssl


@TestStep(Given)
def add_certificate_to_zookeeper_truststore(
    self,
    alias,
    certificate,
    keystore="/truststore.jks",
    storepass="truststore",
    node=None,
):
    """Add certificate to ZooKeeper's truststore."""
    if node is None:
        node = self.context.zookeeper_node

    node.command(
        f"keytool -importcert -alias {alias} "
        f"-file {certificate} "
        f"-keystore {keystore} "
        f"-storepass {storepass} "
        f"-storetype JKS -noprompt",
        exitcode=0,
    )


@TestStep(Given)
def create_zookeeper_crt_and_key(
    self,
    name,
    node=None,
    keystore="/keystore.jks",
    keyalg="RSA",
    keysize=2048,
    storepass="keystore",
    keypass=None,
):
    """Create zookeeper certificate and key. Key is stored in the keystore."""
    if node is None:
        node = self.context.zookeeper_node

    with By("generating keypair"):
        command = (
            f"keytool -genkeypair -alias {name} "
            f"-keyalg {keyalg} "
            f"-keystore {keystore} "
            f"-keysize {keysize} "
            f'-dname "CN=$(hostname -f),OU=Dept,O=Example.com,L=City,ST=State,C=US" '
            f"-storepass {storepass}"
        )

        if keypass is not None:
            command += f" -keypass {keypass}"

        node.command(command, exitcode=0)

    csr = f"/{name}.csr"

    with And("generating certificate signing request"):
        command = (
            f"keytool -certreq -alias {name} "
            f"-keystore {keystore} "
            f"-file {csr} -storepass {storepass}"
        )

        if keypass is not None:
            command += f" -keypass {keypass}"

        node.command(command, exitcode=0)

    crt = f"/{name}.crt"

    with And("signing the certificate with CA"):
        crt = sign_certificate(
            outfile=crt,
            csr=csr,
            ca_certificate=self.context.zookeeper_node_ca_crt,
            ca_key=self.context.zookeeper_node_ca_key,
            ca_passphrase="",
            node=node.name,
            use_stash=False,
        )

    with And("validating the certificate"):
        validate_certificate(
            certificate=crt,
            ca_certificate=self.context.zookeeper_node_ca_crt,
            node=node,
        )

    with And("adding CA certificate to keystore"):
        add_certificate_to_zookeeper_truststore(
            alias="ca",
            certificate=self.context.zookeeper_node_ca_crt,
            keystore=keystore,
            storepass=storepass,
        )

    with And("adding signed certificate to keystore"):
        add_certificate_to_zookeeper_truststore(
            alias="server", certificate=crt, keystore=keystore, storepass=storepass
        )


class ZooKeeperConfig:
    def __init__(self, content, prev_content, path, name, uid):
        self.content = content
        self.prev_content = prev_content
        self.path = path
        self.name = name
        self.uid = uid


@TestStep(Given)
def create_zookeeper_config_content(self, entries, config_file, config_dir, node):
    """Crate ZooKeeper configuration file."""
    uid = getuid()
    path = os.path.join(config_dir, config_file)
    name = config_file

    with By(f"reading current configuration file", description=f"{path}"):
        current_content = node.command(f"cat {path}").output.strip()

    with And("parsing current config content"):
        for line in current_content.splitlines():
            key, value = [p.strip() for p in line.split("=", 1)]
            if not key in entries:
                entries[key] = value

    with And("creating new config content"):
        content = define(
            "content",
            "\n".join([f"{k}={v}" for k, v in entries.items() if v is not None]),
        )

    return ZooKeeperConfig(content, current_content, path, name, uid)


@TestStep(Given)
def add_zookeeper_config(self, config, timeout, restart, node):
    """Add ZooKeeper configuration file."""
    try:
        with When("I add the config", description=config.path):
            command = f"cat <<HEREDOC > {config.path}\n{config.content}\nHEREDOC"
            node.command(command, steps=False, exitcode=0)

        if restart:
            with And("I restart zookeeper server"):
                node.restart_zookeeper(timeout=timeout)

        yield
    finally:
        with Finally("I restore configuration file to the original"):
            with By("adding old config", description=config.path):
                command = (
                    f"cat <<HEREDOC > {config.path}\n{config.prev_content}\nHEREDOC"
                )
                node.command(command, steps=False, exitcode=0)

        if restart:
            with And("restarting zookeeper server"):
                node.restart_zookeeper(timeout=timeout)


@TestStep(Given)
def add_zookeeper_configuration_file(
    self,
    entries,
    config=None,
    config_dir="/conf",
    config_file="zoo.cfg",
    timeout=300,
    restart=True,
    node=None,
):
    if node is None:
        node = self.context.zookeeper_node

    """Add or update ZooKeeper configuration file."""
    if config is None:
        config = create_zookeeper_config_content(
            entries=entries, config_file=config_file, config_dir=config_dir, node=node
        )

    return add_zookeeper_config(
        config=config, timeout=timeout, restart=restart, node=node
    )


@TestStep(Given)
def add_secure_zookeeper_configuration_file(
    self,
    port="2281",
    config=None,
    config_d_dir="/etc/clickhouse-server/config.d",
    config_file="zookeeper_secure.xml",
    timeout=300,
    restart=False,
    node=None,
):
    """Add secure ZooKeeper configuration to config.xml."""
    self.context.secure_zookeeper_port = port

    entries = {
        "zookeeper": {
            "node": {"host": "zookeeper", "port": f"{port}", "secure": "1"},
            "session_timeout_ms": "15000",
        }
    }

    if config is None:
        config = create_xml_config_content(
            entries, config_file=config_file, config_d_dir=config_d_dir
        )

    return add_config(config, timeout=timeout, restart=restart, node=node)


@TestStep(When)
def check_clickhouse_connection_to_zookeeper(self, node=None):
    """Check ClickHouse connection to ZooKeeper."""

    if node is None:
        node = self.context.node

    node.query("SELECT * FROM system.zookeeper WHERE path = '/' FORMAT JSON")


@TestFeature
@Name("zookeeper")
def feature(self, node="clickhouse1", zookeeper_node="zookeeper"):
    """Check configuring and using SSL connection to ZooKeeper."""
    self.context.node = self.context.cluster.node(node)
    self.context.zookeeper_node = self.context.cluster.node(zookeeper_node)

    with Given("I enable SSL on clickhouse"):
        enable_ssl(my_own_ca_key_passphrase="", server_key_passphrase="")

    with And("I generate clickhouse client private key and certificate"):
        create_crt_and_key(name="client", node=self.context.node)

    with And("I add CA certificate to zookeeper node"):
        zookeeper_node_ca_crt = add_trusted_ca_certificate(
            node=self.context.zookeeper_node, certificate=self.context.my_own_ca_crt
        )
        self.context.zookeeper_node_ca_crt = zookeeper_node_ca_crt

    with And(
        "I copy the CA key to zookeeper for certificate signing",
        description=f"{self.context.zookeeper_node}",
    ):
        self.context.zookeeper_node_ca_key = "/my_own_ca.key"
        copy(
            dest_node=self.context.zookeeper_node,
            src_path=self.context.my_own_ca_key,
            dest_path=self.context.zookeeper_node_ca_key,
        )

    with And("I generate zookeeper server private key and certificate"):
        create_zookeeper_crt_and_key(name="server", node=self.context.zookeeper_node)

    with And("I add CA certificate to zookeeper truststore"):
        add_certificate_to_zookeeper_truststore(
            alias="my_own_ca", certificate=self.context.zookeeper_node_ca_crt
        )

    with And("I add ClickHouse SSL server acting as client configuration"):
        entries = {
            "certificateFile": "/client.crt",
            "privateKeyFile": "/client.key",
            "loadDefaultCAFile": "true",
            "cacheSessions": "false",
            "disableProtocols": "sslv2,sslv3",
            "preferServerCiphers": "true",
            "verificationMode": "strict",
            "invalidCertificateHandler": {"name": "RejectCertificateHandler"},
        }
        add_ssl_client_configuration_file(entries=entries)

    with And("I update zookeeper configuration to use encryption"):
        entries = {
            "clientPort": None,
            "secureClientPort": "2281",
            "serverCnxnFactory": "org.apache.zookeeper.server.NettyServerCnxnFactory",
            "ssl.keyStore.location": "/keystore.jks",
            "ssl.keyStore.password": "keystore",
            "ssl.trustStore.location": "/truststore.jks",
            "ssl.trustStore.password": "truststore",
        }
        add_zookeeper_configuration_file(entries=entries)

    with And("I add secure zookeeper configuration"):
        add_secure_zookeeper_configuration_file(restart=True)

    with Then("I check ClickHouse connection to zookeeper"):
        check_clickhouse_connection_to_zookeeper()
