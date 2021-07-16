from wafp.targets import BaseTarget, Metadata


class Default(BaseTarget):
    def get_base_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/api/v1"

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/apispec.json"

    def is_ready(self, line: bytes) -> bool:
        return b"* Running on" in line

    def get_metadata(self) -> Metadata:
        return Metadata.flasgger(
            flask_version="1.0.2", flasgger_version="0.9.1", openapi_version="2.0", validation_from_schema=False
        )


class Linked(Default):
    def get_schema_location(self) -> str:
        # API schema with the following links:
        #  PUT /user/create -> DELETE /user/{username}
        #  PUT /user/create -> GET /user/{username}
        #  PUT /user/create -> POST /user/{username}
        #  PUT /user/create -> PUT /user/{username}
        #  PUT /user/create -> PUT /user/{username}/reset
        #  DELETE /user/{username} -> DELETE /user/{username}
        #  DELETE /user/{username} -> GET /user/{username}
        #  DELETE /user/{username} -> POST /user/{username}
        #  DELETE /user/{username} -> PUT /user/{username}
        #  DELETE /user/{username} -> PUT /user/{username}/reset
        #  GET /user/{username} -> DELETE /user/{username}
        #  GET /user/{username} -> GET /user/{username}
        #  GET /user/{username} -> POST /user/{username}
        #  GET /user/{username} -> PUT /user/{username}
        #  GET /user/{username} -> PUT /user/{username}/reset
        #  POST /user/{username} -> DELETE /user/{username}
        #  POST /user/{username} -> GET /user/{username}
        #  POST /user/{username} -> POST /user/{username}
        #  POST /user/{username} -> PUT /user/{username}
        #  POST /user/{username} -> PUT /user/{username}/reset
        #  PUT /user/{username}/reset -> DELETE /user/{username}
        #  PUT /user/{username}/reset -> GET /user/{username}
        #  PUT /user/{username}/reset -> POST /user/{username}
        #  PUT /user/{username}/reset -> PUT /user/{username}
        #  PUT /user/{username}/reset -> PUT /user/{username}/reset
        return str(self.path / "schema-with-links.json")
