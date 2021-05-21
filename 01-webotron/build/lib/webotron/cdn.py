# -*- coding: utf-8 -*-

"""Classes for Cloud Front DIstributions."""
import uuid

class DistributionManager:
    def __init__(self, session):
        self.session = session
        self.cdn_client = self.session.cliend('cloudfront')
        
    def find_matching_dist(self, domain_name):
        """Find a dist matching domain_name."""
        paginator = self.cdn_client.get_paginator('list_distributions')
        for page in paginator.paginate():
            for dist in page['DistributionList']['Items']:
                for alias in dist['Alias']['Items']:
                    if alias == domain_name:
                        return dist
            
        
    def create_dist(self, domain_name, cert):
        """Create a dist for domain_name using cert."""
        origin_id = 'S3-' + domain_name
        
        
        result = self.cdn_client.create_distribution(
            DistributionConfig={
                'CallerReference': str(uuid.uuid4()),
                'Aliases': {
                    'Quantity': 1,
                    'Items': [domain_name]
                },
                'DefaultRootObject': 'index.html',
                'Comment': 'Created by webotron',
                'Enabled': True,
                'Origins': {
                    'Quantity': 1,
                    'Items': [{
                        'Id': origin_id,
                        'DomainName': f'{domain_name}.s3.amazonaws.com',
                        'S3OriginConfig': {
                            'OriginAccessIdentity': ''
                        }
                    }]
                },
                'DefaultCacheBehaviour': {
                    'TargetOriginId': origin_id,
                    'ViewerProtocolPolicy': 'redirect-to-https',
                    'TrustedSigners': {
                        'Quantity': 0,
                        'Enabled': False
                    },
                    'ForwardValues': {
                        'Cookies': { 'Forward': 'all '},
                        'Headers': { 'Quantity': 0 },
                        'QueryString': False,
                        'QueryStringCacheKeys': { 'Quantity': 0 }
                    },
                    'DefaultTTL': 86400,
                    'MinTTL': 3600
                },
                'ViewerCertificate': {
                    'ACMCertificateArn': cert['CertificateArn'],
                    'SSLSupportMethod': 'sni-only',
                    'MinimumProtocolVersion': 'TLSv1.1_2016'
                }
            }       
        )
        
        return result['Distribution']
            
    def await_deploy(self, dist):
        """Wait for dist to be deployed."""
        waiter = self.cdn_client.get_waiter('distribution_deployed')
        waiter.wait(Id=dist['Id'], WaiterConfig={
            'Delay': 30,
            'MaxAttempts': 50
        })
        
    def create_cf_domain_record(self, zone, domain_name, cf_domain):
        return self.cdn_client.change_resource_record_sets(
            HostedZoneId=zone['Id'],
            ChangeBatch={
                'Comment': 'Created by Webotron',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': domain_name,
                            'Type': 'A',
                            'AliasTarget': {
                                'HostedZoneId': 'Z2FDTNDATAQYW2',
                                'DNSName': cf_domain,
                                'EvaluateTargetHealth': False
                            }
                        }
                    }
                ]
            }
        )