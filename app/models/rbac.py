from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class RolePermission(Base, TimestampMixin):
    __tablename__ = "role_permissions"
    
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), primary_key=True)

    # Relationships to parents
    role: Mapped["Role"] = relationship(back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship(back_populates="role_permissions")

class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    role_permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="role"
    )
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="role")

class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    role_permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="permission"
    )
