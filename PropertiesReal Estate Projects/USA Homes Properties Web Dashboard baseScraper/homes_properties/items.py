# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from scrapy import Field, Item


class HomesPropertiesItem(Item):
    # common fields in db table rent
    Search_Term = Field()
    Address = Field()
    Street = Field()
    City = Field()
    State = Field()
    Zip_Code = Field()
    Latitude = Field()
    Longitude = Field()
    Beds = Field()
    Baths = Field()
    Area = Field()
    Property_Type = Field()
    Price = Field()
    Year_Built = Field()
    Availability_Date = Field()
    Broker = Field()
    Image = Field()
    URL = Field()

    # Coomin in saletable
    SearchTerm = Field()
    Listing_Agent = Field()
    Zipcode = Field()
    Sqft = Field()
    Listing_Office = Field()
    Status = Field()
    Sold_Date = Field()

    # different from db table now save into homesproperties tble
    Agent_Phone = Field()
    Agent_Email = Field()
    Lot_Size_Acres = Field()
    Annual_Tax = Field()
    MLS = Field()
    Broker_Phone = Field()
    Broker_Email = Field()
    Broker_Company = Field()
    Other_Images = Field()

    pass
