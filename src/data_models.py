from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr, HttpUrl


class System(BaseModel):
    id: HttpUrl
    type: str
    oparlVersion: str
    otherOparlVersions: List[HttpUrl]
    license: HttpUrl
    body: HttpUrl
    name: str
    contactEmail: EmailStr
    contactName: str
    website: HttpUrl
    vendor: HttpUrl
    product: HttpUrl
    created: datetime
    modified: datetime
    web: HttpUrl
    deleted: bool


class Location(BaseModel):
    id: HttpUrl
    type: str
    description: str
    geojson: dict
    streetAddress: str
    room: str
    postalCode: str
    subLocality: str
    locality: str
    bodies: List[HttpUrl]
    organizations: List[HttpUrl]
    persons: List[HttpUrl]
    meetings: List[HttpUrl]
    papers: List[HttpUrl]
    license: str
    keyword: List[str]
    created: datetime
    modified: datetime
    web: HttpUrl
    deleted: bool


class LegislativeTerm(BaseModel):
    id: HttpUrl
    type: str
    body: HttpUrl
    name: str
    startDate: datetime
    endDate: datetime
    license: str
    keyword: List[str]
    created: datetime
    modified: datetime
    web: HttpUrl
    deleted: bool


class Organization(BaseModel):
    id: HttpUrl
    type: str
    body: HttpUrl
    name: str
    membership: List[HttpUrl]
    meeting: HttpUrl
    shortName: str
    post: List[str]
    subOrganizationOf: HttpUrl
    organizationType: str
    classification: str
    startDate: datetime
    endDate: datetime
    website: HttpUrl
    location: Location
    externalBody: HttpUrl
    license: str
    keyword: List[str]
    created: datetime
    modified: datetime
    web: HttpUrl
    deleted: bool


class Person(BaseModel):
    id: HttpUrl
    type: str
    body: HttpUrl
    name: str
    familyName: str
    givenName: str
    formOfAddress: str
    affix: str
    title: List[str]
    gender: str
    phone: List[str]
    email: List[str]
    location: HttpUrl
    locationObject: Location
    status: List[str]
    membership: List["Membership"]
    life: str
    lifeSource: str
    license: str
    keyword: List[str]
    created: datetime
    modified: datetime
    web: HttpUrl
    deleted: bool


class Membership(BaseModel):
    id: HttpUrl
    type: str
    person: HttpUrl
    organization: HttpUrl
    role: str
    votingRight: bool
    startDate: datetime
    endDate: datetime
    onBehalfOf: HttpUrl
    license: str
    keyword: List[str]
    created: datetime
    modified: datetime
    web: HttpUrl
    deleted: bool


class Meeting(BaseModel):
    id: HttpUrl
    type: str
    name: str
    meetingState: str
    cancelled: bool
    start: datetime
    end: datetime
    location: Location
    organization: List[HttpUrl]
    participant: List[HttpUrl]
    invitation: dict
    resultsProtocol: dict
    verbatimProtocol: dict
    auxiliaryFile: List[dict]
    agendaItem: List["AgendaItem"]
    license: str
    keyword: List[str]
    created: datetime
    modified: datetime
    web: HttpUrl
    deleted: bool


class AgendaItem(BaseModel):
    id: HttpUrl
    type: str
    meeting: HttpUrl
    number: str
    order: int
    name: str
    public: bool
    result: str
    resolutionText: str
    resolutionFile: dict
    auxiliaryFile: List[dict]
    start: datetime
    end: datetime
    license: str
    keyword: List[str]
    created: datetime
    modified: datetime
    web: HttpUrl
    deleted: bool


class Paper(BaseModel):
    id: HttpUrl
    type: str
    body: HttpUrl
    name: str
    reference: str
    date: datetime
    paperType: str
    relatedPaper: List[HttpUrl]
    superordinatedPaper: List[HttpUrl]
    subordinatedPaper: List[HttpUrl]
    mainFile: dict
    auxiliaryFile: List[dict]
    location: List[Location]
    originatorPerson: List[HttpUrl]
    underDirectionOf: List[HttpUrl]
    originatorOrganization: List[HttpUrl]
    license: str
    keyword: List[str]
    created: datetime
    modified: datetime
    web: HttpUrl
    deleted: bool


class File(BaseModel):
    id: HttpUrl
    type: str
    name: str
    fileName: str
    mimeType: str
    date: datetime
    size: int
    sha1Checksum: str
    sha512Checksum: str
    text: str
    accessUrl: HttpUrl
    downloadUrl: HttpUrl
    externalServiceUrl: HttpUrl
    masterFile: HttpUrl
    derivativeFile: List[HttpUrl]
    fileLicense: HttpUrl
    meeting: List[HttpUrl]
    agendaItem: List[HttpUrl]
    paper: List[HttpUrl]
    license: str
    keyword: List[str]
    created: datetime
    modified: datetime
    web: HttpUrl
    deleted: bool


class Body(BaseModel):
    """Körperschaft, z.B. Stadt, Gemeinde oder Landkreis"""

    id: HttpUrl
    type: str
    name: str
    shortName: str
    system: HttpUrl
    website: HttpUrl
    license: HttpUrl
    licenseValidSince: datetime
    oparlSince: datetime
    ags: str
    rgs: str
    equivalent: List[HttpUrl]
    contactEmail: str
    contactName: str
    organization: HttpUrl
    person: HttpUrl
    meeting: HttpUrl
    paper: HttpUrl
    legislativeTerm: LegislativeTerm
    agendaItem: HttpUrl
    file: HttpUrl
    locationList: HttpUrl
    legislativeTermList: HttpUrl
    membership: HttpUrl
    classification: str
    location: Location
    keyword: List[str]
    created: datetime
    modified: datetime
    web: HttpUrl
    deleted: bool


# Forward references for Membership and AgendaItem
Person.model_rebuild()
Meeting.model_rebuild()
AgendaItem.model_rebuild()
