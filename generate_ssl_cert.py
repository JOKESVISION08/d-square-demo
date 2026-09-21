"""
SSL Certificate Generator for D-SQUARE 2.0
Generates self-signed cert.pem and key.pem for HTTPS secure origin streaming.
Enables continuous mobile camera stream on iOS Safari & Android Chrome without flags.
"""

import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import ipaddress

CERT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cert.pem")
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "key.pem")

def generate_self_signed_cert():
    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        print(f"[SSL] Using existing SSL certificate: {CERT_FILE}")
        return CERT_FILE, KEY_FILE

    print("[SSL] Generating self-signed TLS/SSL certificate for secure mobile camera streaming...")
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Uttarakhand"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "ISRO-Bhuvan"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "D-SQUARE 2.0 AI Surveillance"),
        x509.NameAttribute(NameOID.COMMON_NAME, "10.172.49.122"),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            x509.IPAddress(ipaddress.IPv4Address("10.172.49.122")),
        ]),
        critical=False,
    ).sign(key, hashes.SHA256())

    with open(KEY_FILE, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with open(CERT_FILE, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"[SSL SUCCESS] Generated cert: {CERT_FILE}, key: {KEY_FILE}")
    return CERT_FILE, KEY_FILE

if __name__ == "__main__":
    generate_self_signed_cert()
