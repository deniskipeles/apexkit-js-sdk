import requests
import json
from typing import Optional, List, Dict, Any, Union, BinaryIO
from .models import (
    ScopeType, User, AuthResponse, BaseRecord, ListResult, Collection,
    StoredFile, InstantResult, Script, Template, AiAction, AiSession,
    Plugin, ApiKey, SystemLog, SiteFile, Scope
)
from .exceptions import ApexError

class ApexKit:
    def __init__(self, base_url: str, scope_type: str = 'root', scope_id: str = ''):
        self.base_url = base_url.rstrip("/")
        self.scope_type = scope_type
        self.scope_id = scope_id
        self.token = None
        self.current_user = None

    @property
    def scope(self) -> Scope:
        return Scope(type=self.scope_type, id=self.scope_id)

    def sandbox(self, uuid: str) -> 'ApexKit':
        sandbox_url = f"{self.base_url}/sandbox/{uuid}"
        instance = ApexKit(sandbox_url, 'sandbox', uuid)
        instance.set_token(self.token, self.current_user)
        return instance

    def tenant(self, tenant_id: str) -> 'ApexKit':
        tenant_url = f"{self.base_url}/tenant/{tenant_id}"
        instance = ApexKit(tenant_url, 'tenant', tenant_id)
        instance.set_token(self.token, self.current_user)
        return instance

    def set_token(self, token: str, user: Optional[Dict[str, Any]] = None):
        self.token = token
        if user:
            self.current_user = user
            if user.get('scope'):
                self._set_scope_from_tag(user['scope'])

    def _set_scope_from_tag(self, tag: str):
        if tag == 'root':
            self.scope_type = 'root'
            self.scope_id = ''
        elif tag.startswith('tenant:'):
            self.scope_type = 'tenant'
            self.scope_id = tag.split(':')[1] if ':' in tag else ''
        elif tag.startswith('sandbox:'):
            self.scope_type = 'sandbox'
            self.scope_id = tag.split(':')[1] if ':' in tag else ''

    def get_token(self) -> Optional[str]:
        return self.token

    def get_user(self) -> Optional[Dict[str, Any]]:
        return self.current_user

    def _request(self, endpoint: str, method: str = 'GET', headers: Dict[str, str] = None,
                 body: Any = None, params: Dict[str, Any] = None, is_root: bool = False,
                 files: Any = None, stream: bool = False):
        path = endpoint
        if not is_root and not endpoint.startswith('/api/v1'):
            path = f"/api/v1/{endpoint.lstrip('/')}"

        url = f"{self.base_url}{path}"

        req_headers = headers.copy() if headers else {}
        if self.token:
            req_headers['Authorization'] = f"Bearer {self.token}"

        if body and not files and not isinstance(body, (bytes, str)):
            req_headers['Content-Type'] = 'application/json'
            body = json.dumps(body)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=req_headers,
                data=body if not files else None,
                params=params,
                files=files,
                stream=stream
            )

            if response.status_code == 204:
                return None

            content_type = response.headers.get("content-type", "")
            if "text/plain" in content_type or "text/html" in content_type:
                if not response.ok:
                    raise ApexError(response.text, response.status_code)
                return response.text

            if stream:
                return response

            try:
                data = response.json()
            except ValueError:
                if not response.ok:
                    raise ApexError(response.text, response.status_code)
                return response.text

            if is_root and isinstance(data, dict) and 'errors' in data:
                raise ApexError(data['errors'][0].get('message', 'GraphQL Error'), 400, 'graphql_error', data['errors'])

            if not response.ok:
                raise ApexError(
                    data.get('message', 'API Error'),
                    response.status_code,
                    data.get('error'),
                    data.get('details')
                )

            return data
        except requests.exceptions.RequestException as e:
            if isinstance(e, ApexError):
                raise e
            raise ApexError(str(e))

    @property
    def auth(self):
        class AuthNamespace:
            def __init__(self, client: 'ApexKit'):
                self.client = client

            def list_roles(self):
                return self.client._request('/auth/roles')

            def login(self, email: str, password: str):
                res = self.client._request('/auth/login', method='POST', body={'email': email, 'password': password})
                self.client.token = res['token']
                self.client.current_user = res['user']
                if res['user'].get('scope'):
                    self.client._set_scope_from_tag(res['user']['scope'])
                return res

            def register(self, email: str, password: str):
                res = self.client._request('/auth/register', method='POST', body={'email': email, 'password': password})
                self.client.token = res['token']
                self.client.current_user = res['user']
                return res

            def get_me(self):
                user = self.client._request('/auth/me')
                if user.get('scope'):
                    self.client._set_scope_from_tag(user['scope'])
                return user

            def logout(self):
                self.client.token = None
                self.client.current_user = None

            def login_with_github(self, redirect_to: str = None):
                path = '/api/v1/auth/github'
                params = f"?redirect_to={redirect_to}" if redirect_to else ""
                return f"{self.client.base_url}{path}{params}"

            def login_with_google(self, redirect_to: str = None):
                path = '/api/v1/auth/google'
                params = f"?redirect_to={redirect_to}" if redirect_to else ""
                return f"{self.client.base_url}{path}{params}"

        return AuthNamespace(self)

    @property
    def admins(self):
        class AdminsNamespace:
            def __init__(self, client: 'ApexKit'):
                self.client = client

            # Collections
            def list_collections(self):
                return self.client._request('/collections')
            def create_collection(self, name: str, schema: any):
                return self.client._request('/collections', method='POST', body={'name': name, 'schema': schema})
            def get_collection(self, id: Union[str, int]):
                return self.client._request(f'/collections/{id}')
            def update_collection(self, id: Union[str, int], payload: any):
                return self.client._request(f'/collections/{id}', method='PUT', body=payload)
            def patch_collection(self, id: Union[str, int], payload: any):
                return self.client._request(f'/collections/{id}', method='PATCH', body=payload)
            def delete_collection(self, id: Union[str, int]):
                return self.client._request(f'/collections/{id}', method='DELETE')

            # Config
            def list_configs(self):
                return self.client._request('/admin/config')
            def set_config(self, key: str, value: str, encrypt: bool):
                return self.client._request('/admin/config', method='POST', body={'key': key, 'value': value, 'encrypt': encrypt})
            def delete_config(self, key: str):
                import urllib.parse
                return self.client._request(f'/admin/config/{urllib.parse.quote(key)}', method='DELETE')

            # Users
            def register_user(self, email: str, password: str = None, role: str = None, metadata: any = None):
                return self.client._request('/auth/register', method='POST', body={'email': email, 'password': password, 'role': role, 'metadata': metadata})
            def update_user(self, id: Union[str, int], email: str = None, password: str = None, role: str = None, metadata: any = None):
                return self.client._request(f'/admin/users/{id}', method='PATCH', body={'email': email, 'password': password, 'role': role, 'metadata': metadata})
            def list_users(self, options: Dict[str, Any] = None):
                return self.client._request('/admin/users', params=options)
            def delete_user(self, id: Union[str, int]):
                return self.client._request(f'/admin/users/{id}', method='DELETE')

            # Settings
            def get_settings(self):
                return self.client._request('/admin/settings')
            def update_settings(self, settings: any):
                return self.client._request('/admin/settings', method='PUT', body=settings)
            def patch_settings(self, settings: any):
                return self.client._request('/admin/settings', method='PATCH', body=settings)

            # Storage Utils
            def test_s3_storage_connection(self, config: any):
                return self.client._request('/admin/storage/test', method='POST', body=config)
            def migrate_storage(self, source: str, destination: str):
                return self.client._request('/admin/storage/migrate', method='POST', body={'source': source, 'destination': destination})

            # Backups
            def create_backup(self):
                return self.client._request('/admin/backup', method='POST')
            def list_backups(self):
                return self.client._request('/admin/backups')
            def restore_from_file(self, filename: str):
                return self.client._request('/admin/restore-file', method='POST', body={'filename': filename})
            def restore_backup(self, file: BinaryIO):
                return self.client._request('/admin/restore', method='POST', files={'file': file})
            def download_backup(self, filename: str):
                return self.client._request(f'/admin/backups/{filename}', stream=True)

            # API Keys
            def list_api_keys(self):
                return self.client._request('/admin/keys')
            def create_api_key(self, name: str, role: str = 'admin', scope: str = 'root', bypass_cors: bool = True):
                return self.client._request('/admin/keys', method='POST', body={'name': name, 'role': role, 'scope': scope, 'bypass_cors': bypass_cors})
            def update_api_key(self, id: Union[str, int], updates: any):
                return self.client._request(f'/admin/keys/{id}', method='PUT', body=updates)
            def delete_api_key(self, id: Union[str, int]):
                return self.client._request(f'/admin/keys/{id}', method='DELETE')

            # System
            def reload_system(self, target: str = None):
                return self.client._request('/admin/system/reload', method='POST', body={'target': target})
            def test_email(self, email: str):
                return self.client._request('/admin/smtp/test', method='POST', body={'email': email})
            def re_index(self, collection_id: Union[str, int] = ''):
                return self.client._request(f'/admin/collections/{collection_id}/reindex', method='POST', body={})
            def revectorize_collection(self, collection_id: Union[str, int]):
                return self.client._request(f'/admin/collections/{collection_id}/revectorize', method='POST', body={'force': False})

            # Import/Export
            def import_data(self, collection_name: str, file: BinaryIO):
                return self.client._request('/admin/import-data', method='POST', files={'collection_name': (None, collection_name), 'file': file})
            def import_schema(self, file: BinaryIO, strategy: str = 'skip'):
                return self.client._request('/admin/import-schema', method='POST', files={'strategy': (None, strategy), 'file': file})
            def export_schema(self):
                return self.client._request('/admin/export-schema', stream=True)
            def get_dashboard_stats(self):
                return self.client._request('/admin/dashboard')

            # Tenant Admin Ops
            def create_tenant(self, tenant_id: str):
                return self.client._request('/admin/tenants', method='POST', body={'tenant_id': tenant_id})
            def delete_tenant(self, id: str):
                return self.client._request(f'/admin/tenants/{id}', method='DELETE')
            def update_tenant(self, id: str, data: any):
                return self.client._request(f'/admin/tenants/{id}', method='PATCH', body=data)
            def list_tenants(self):
                return self.client._request('/admin/tenants')
            def update_tenant_status(self, id: str, status: str):
                return self.client._request(f'/admin/tenants/{id}/status', method='PATCH', body={'status': status})

        return AdminsNamespace(self)

    @property
    def ai(self):
        class AiNamespace:
            def __init__(self, client: 'ApexKit'):
                self.client = client

            def get_actions(self):
                return self.client._request('/admin/ai/actions')
            def create_action(self, data: Dict[str, Any]):
                return self.client._request('/admin/ai/actions', method='POST', body=data)
            def delete_action(self, id: Union[str, int]):
                return self.client._request(f'/admin/ai/actions/{id}', method='DELETE')
            def run(self, slug: str, variables: Dict[str, Any]):
                return self.client._request(f'/ai/run/{slug}', method='POST', body={'variables': variables})

            # Architect
            def list_sessions(self):
                return self.client._request('/admin/ai/sessions')
            def create_session(self, name: str, initial_prompt: str = None, model: str = None, clone_strategy: str = None, clone_record_limit: int = None):
                return self.client._request('/admin/ai/sessions', method='POST', body={
                    'name': name, 'initial_prompt': initial_prompt, 'model': model,
                    'clone_strategy': clone_strategy, 'clone_record_limit': clone_record_limit
                })
            def delete_session(self, id: str):
                return self.client._request(f'/admin/ai/sessions/{id}', method='DELETE')
            def chat(self, session_id: str, prompt: str, model: str):
                return self.client._request(f'/admin/ai/sessions/{session_id}/chat', method='POST', body={'prompt': prompt, 'model': model})
            def apply_session_changes(self, session_id: str):
                return self.client._request(f'/admin/ai/sessions/{session_id}/apply', method='POST')
            def publish_session(self, session_id: str):
                return self.client._request(f'/admin/ai/sessions/{session_id}/publish', method='POST')

            def list_plugins(self):
                return self.client._request('/ai/plugins')

            def edit_code(self, prompt: str, current_code: str, context_type: str, model: str):
                return self.client._request('/admin/ai/edit-code', method='POST', body={
                    'prompt': prompt, 'current_code': current_code, 'context_type': context_type, 'model': model
                })

            def export_actions(self):
                return self.client._request('/admin/export-ai-actions', stream=True)
            def import_actions(self, file: BinaryIO):
                return self.client._request('/admin/import-ai-actions', method='POST', files={'file': file})

        return AiNamespace(self)

    @property
    def scripts(self):
        class ScriptsNamespace:
            def __init__(self, client: 'ApexKit'):
                self.client = client

            def list(self):
                return self.client._request('/admin/scripts')
            def create(self, data: Dict[str, Any]):
                return self.client._request('/admin/scripts', method='POST', body=data)
            def delete(self, id: Union[str, int]):
                return self.client._request(f'/admin/scripts/{id}', method='DELETE')
            def run(self, name: str, variables: any):
                return self.client._request(f'/run/{name}', method='POST', body=variables)
            def export(self):
                return self.client._request('/admin/export-scripts', stream=True)
            def import_scripts(self, file: BinaryIO):
                return self.client._request('/admin/import-scripts', method='POST', files={'file': file})

        return ScriptsNamespace(self)

    @property
    def templates(self):
        class TemplatesNamespace:
            def __init__(self, client: 'ApexKit'):
                self.client = client

            def list(self):
                return self.client._request('/admin/templates')
            def create(self, data: Dict[str, Any]):
                return self.client._request('/admin/templates', method='POST', body=data)
            def update(self, id: Union[str, int], data: Dict[str, Any]):
                return self.client._request(f'/admin/templates/{id}', method='PUT', body=data)
            def delete(self, id: Union[str, int]):
                return self.client._request(f'/admin/templates/{id}', method='DELETE')
            def export(self):
                return self.client._request('/admin/export-templates', stream=True)
            def import_templates(self, file: BinaryIO):
                return self.client._request('/admin/import-templates', method='POST', files={'file': file})

        return TemplatesNamespace(self)

    def collection(self, collection_id: Union[str, int]):
        class CollectionNamespace:
            def __init__(self, client: 'ApexKit', cid: Union[str, int]):
                self.client = client
                self.cid = cid

            def list(self, options: Dict[str, Any] = None):
                return self.client._request(f'/collections/{self.cid}/records', params=options)
            def search_records_with_sql(self, query: any):
                return self.client._request(f'/collections/{self.cid}/query', method='POST', body={'query': query})
            def search_records_with_ose(self, query: str):
                return self.client._request(f'/collections/{self.cid}/search', params={'q': query})
            def search_records_instantly_with_ose(self, query: str):
                return self.client._request(f'/collections/{self.cid}/instant-search', params={'q': query})
            def create(self, data: any):
                return self.client._request(f'/collections/{self.cid}/records', method='POST', body={'data': data})
            def get(self, record_id: Union[str, int], options: Dict[str, Any] = None):
                return self.client._request(f'/collections/{self.cid}/records/{record_id}', params=options)
            def update(self, record_id: Union[str, int], data: any):
                return self.client._request(f'/collections/{self.cid}/records/{record_id}', method='PUT', body={'data': data})
            def patch(self, record_id: Union[str, int], data: any):
                return self.client._request(f'/collections/{self.cid}/records/{record_id}', method='PATCH', body={'data': data})
            def delete(self, record_id: Union[str, int]):
                return self.client._request(f'/collections/{self.cid}/records/{record_id}', method='DELETE')
            def add_relation(self, origin_record_id: Union[str, int], target_collection_id: Union[str, int], target_record_id: Union[str, int], relation_name: str):
                return self.client._request(f'/collections/{self.cid}/records/{origin_record_id}/relations', method='POST', body={
                    'target_collection_id': int(target_collection_id), 'target_record_id': int(target_record_id), 'relation_name': relation_name
                })
            def remove_relation(self, origin_record_id: Union[str, int], target_collection_id: Union[str, int], target_record_id: Union[str, int], relation_name: str):
                return self.client._request(f'/collections/{self.cid}/records/{origin_record_id}/relations', method='DELETE', body={
                    'target_collection_id': int(target_collection_id), 'target_record_id': int(target_record_id), 'relation_name': relation_name
                })
            def search_vector(self, field: str, vector: List[float], limit: int = 10):
                return self.client._request(f'/collections/{self.cid}/search-vector', method='POST', body={'field': field, 'vector': vector, 'limit': limit})
            def search_text_vector(self, query_text: str, limit: int = 10):
                return self.client._request(f'/collections/{self.cid}/search-text-vector', method='POST', body={'query_text': query_text, 'limit': limit})
            def search_image_vector(self, image_data: str, limit: int = 10):
                return self.client._request(f'/collections/{self.cid}/search-image-vector', method='POST', body={'image_data': image_data, 'limit': limit})
            def get_vector(self, record_id: Union[str, int]):
                return self.client._request(f'/collections/{self.cid}/get-vector/{record_id}')

        return CollectionNamespace(self, collection_id)

    @property
    def files(self):
        class FilesNamespace:
            def __init__(self, client: 'ApexKit'):
                self.client = client

            def list(self, page: int = 1, per_page: int = 20):
                return self.client._request('/storage/files', params={'page': page, 'per_page': per_page})
            def upload(self, file: BinaryIO):
                return self.client._request('/storage/upload', method='POST', files={'file': file})
            def delete(self, id: Union[str, int]):
                return self.client._request(f'/storage/files/{id}', method='DELETE')
            def get_file_url(self, filename: str) -> str:
                if filename.startswith('http://') or filename.startswith('https://'):
                    return filename
                base = self.client.base_url.rstrip("/")
                name = filename.lstrip("/")
                return f"{base}/api/v1/storage/file/{name}"

        return FilesNamespace(self)

    @property
    def logs(self):
        class LogsNamespace:
            def __init__(self, client: 'ApexKit'):
                self.client = client
            def list(self):
                return self.client._request('/admin/logs')
        return LogsNamespace(self)

    def graphql(self, query: str, variables: Dict[str, Any] = None):
        return self._request('/graphql', method='POST', is_root=True, body={'query': query, 'variables': variables or {}})

    @property
    def utils(self):
        class UtilsNamespace:
            def strip_html_tags(self, html: str) -> str:
                import re
                if not html: return ''
                return re.sub(r'<[^>]*>?', '', html)
        return UtilsNamespace()

    @property
    def sites(self):
        class SitesNamespace:
            def __init__(self, client: 'ApexKit'):
                self.client = client
            def deploy(self, file: BinaryIO):
                return self.client._request('/admin/site/deploy', method='POST', files={'file': file})
            def list_files(self):
                return self.client._request('/admin/site/files')
            def delete(self, path: str):
                return self.client._request('/admin/site/files', method='DELETE', params={'path': path})
        return SitesNamespace(self)
