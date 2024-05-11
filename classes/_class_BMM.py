import os
import json
import uuid
import asyncio
import _class_storage as Storage

class BusinessModel():
    def __init__(self):
        self.storage = Storage.PsqlSimpleStorage()

    def _create_model_dict(self, model_data_dict):
        new_model = {
            'id': model_data_dict.get('id', f"{uuid.uuid4()}"),
            'modelName': "",
            'modelDescription': "",
        }
        new_model.update(model_data_dict)
        return new_model

    def _create_entity_dict(self, model_id, endity_data_dict):
        new_entity = {
            'id': endity_data_dict.get('id', f"{uuid.uuid4()}"),
            'modelId': model_id,
            'entityName': "",
            'entityDescription': "",
        }
        new_entity.update(endity_data_dict)
        return new_entity

    def _create_attribute_dict(self, entity_id, attribute_data_dict):
        new_attribute = {
            'id': attribute_data_dict.get('id', f"{uuid.uuid4()}"),
            'entityId': entity_id,
            'attributeName': "",
            'attributeDescription': "",
            'attributeType': "",
            'singleOrMulti': "",
            'aggregationFunction': "",
            'minCharLength': "",
            'editable': "",
            'defaultFieldFormat': "",
        }
        new_attribute.update(attribute_data_dict)
        return new_attribute

    def get_model_list(self):
        model_list = asyncio.run(self.storage.get_data(partitionkey="bmm_model"))
        return model_list
    
    def get_entity_list(self, model_id):
        entity_list = asyncio.run(self.storage.get_data(partitionkey=model_id))
        return entity_list

    def get_attribute_list(self, entity_id):
        attribute_list = asyncio.run(self.storage.get_data(partitionkey=entity_id))
        return attribute_list

    def save_model(self, model_data_dict):
        if model_data_dict.get('id') is None:
            model_data = self._create_model_dict(model_data_dict)
        else:
            model_data = model_data_dict
        data_dict = {
            "partitionkey": 'bmm_model',
            "rowkey": model_data['id'],
            "structdata": model_data
        }
        asyncio.run(self.storage.upsert_data(data_dict))
        return data_dict

    def save_attribute(self, entity_id, attribute_data_dict):
        if attribute_data_dict.get('id') is None:
            attribute_data = self._create_attribute_dict(entity_id, attribute_data_dict)
        else:
            attribute_data = attribute_data_dict
        
        data_dict = {
            "partitionkey": entity_id,
            "rowkey": attribute_data['attributeId'],
            "structdata": attribute_data
        }
        asyncio.run(self.storage.upsert_data(data_dict))
        return data_dict

    def delete_model(self, pkey_rkey_records):
        asyncio.run(self.storage.delete_data(pkey_rkey_records))    
        
    def save_entity(self, model_id, enity_data_dict):
        if enity_data_dict.get('id') is None:
            entity_data = self._create_entity_dict(model_id, enity_data_dict)
        else:
            entity_data = enity_data_dict
        
        data_dict = {
            "partitionkey": model_id,
            "rowkey": entity_data['entityId'],
            "structdata": entity_data
        }
        asyncio.run(self.storage.upsert_data(data_dict))
        return data_dict

