from pydantic import BaseModel, Field

class RoleBase(BaseModel):
    name: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=255)

class RoleCreate(RoleBase):
    pass

class RoleRead(RoleBase):
    id: int

class PermissionBase(BaseModel):
    name: str = Field(..., max_length=50, pattern=r".+:.+")

class PermissionCreate(PermissionBase):
    pass

class PermissionRead(PermissionBase):
    id: int
