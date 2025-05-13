from configparser import ConfigParser
from pathlib import Path

def load_config(config_path='config/config.ini'):
    config = ConfigParser()
    config.read(config_path)
    
    # API settings
    api_config = {
        'url': config['API']['url'],
        'key': config['API']['key'],
        'headers': {
            "x-api-key": config['API']['key'],
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        'model_kwargs': {
            "maxTokens": int(config['API']['max_tokens']),
            "temperature": float(config['API']['temperature']),
            "streaming": False,
            "top_p": float(config['API']['top_p'])
        },
        'request_delay': float(config['API']['request_delay']) / 2
    }
    
    # Processing settings
    processing_config = {
        'supported_extensions': config['PROCESSING']['supported_extensions'].split(','),
        'max_file_size_mb': float(config['PROCESSING']['max_file_size_mb']),
        'output_excel': config['PROCESSING'].get('output_excel', 'resume_analysis.xlsx')
    }
    
    return api_config, processing_config