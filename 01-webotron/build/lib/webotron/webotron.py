#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Webotron: Deploy websites with AWS.

Webotron automates the process of deploying static web.
- Configure AWS S3 buckets.
    - Create them.
    - Set them up for static website hosting.
    - Deploy local files to them.
- Configure DNS with AWS Route 53.
- Configure a Content Delivery Network and SSL with AWS CloudFront.
"""

import boto3
# from botocore.exceptions import ClientError

import click

from webotron.bucket import BucketManager
from webotron.domain import DomainManager
from webotron.certificate import CertificateManager
from webotron.cdn import DistributionManager

from webotron import util



session = None
bucket_manager = None
domain_manager = None
cert_manager = None
dist_manager = None

@click.group()
@click.option('--profile', default=None, help='Use a given AWS profile.')
def cli(profile):
    """Webotron deploys website to AWS."""
    global session, bucket_manager, domain_manager

    session_cfg = {}
    if profile:
        session_cfg['profile_name'] = profile
    session = boto3.Session(**session_cfg)
    bucket_manager = BucketManager(session)
    domain_manager = DomainManager(session)
    cert_manager = CertificateManager(session)
    dist_manager = DistributionManager(session)


@cli.command('list-buckets')
def list_buckets():
    """List all AWS S3 buckets."""
    for bucket in bucket_manager.all_buckets():
        print(bucket)


@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_buckets_object(bucket):
    """List object in an AWS S3 bucket."""
    for obj in bucket_manager.all_objects(bucket):
        print(obj)


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """Create and configure AWS S3 bucket."""
    s3_bucket = bucket_manager.init_bucket(bucket)
    bucket_manager.set_policy(s3_bucket)
    bucket_manager.configure_website()


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Sync contents of PATHNAME to BUCKET."""
    bucket_manager.sync(pathname, bucket)
    print(bucket_manager.get_bucket_url(bucket_manager.s3.Bucket(bucket)))
    
@cli.command('setup-domain')
@click.argument('domain')
@click.argument('bucket')
def setup_domain(domain, bucket):
    """Configure DOMAIN to point to BUCKET"""
    bucket = bucket_manager.get_bucket(domain)
    zone = domain_manager.find_hosted_zone(domain) \
        or domain_manager.create_hosted_zone(domain)
    
    endpoint = util.get_endpoint(bucket_manager.get_region_name(bucket))
    domain_manager.create_s3_domain_record(zone, domain, endpoint)
    print(f"Domain configured: http://{domain}")
    

@cli.command('find-cert')
@click.argument('domain')
def find_cert(domain):
    print(cert_manager)
    

@cli.command('setup-cdn')
@click.argument('domain')
@click.argument('bucket')
def setup_cdn(domain, bucket):
    dist = dist_manager.find_matching_dist(domain)
    
    if not dist:
        cert = cert_manager.find_maching_cert(domain)
        if not cert:
            print("Error: No matching cert found.")
            return
        
        dist = dist_manager.create_dist(domain, cert)
        print("Waiting for distribution deployment...")
        dist_manager.await_deploy(dist)
        
    zone = domain_manager.find_hosted_zone(domain) \
    or domain_manager.create_hosted_zone(domain)
    
    domain_manager.create_cf_domain_record(zone, domain, dist['DomainName'])
    print(f'Domain configure: https://{domain}')
    
    return


if __name__ == "__main__":
    cli()
