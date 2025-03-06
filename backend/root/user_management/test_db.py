from django.db import IntegrityError
from django.test import TestCase
from user_management.models import User, Plants, Gardens, Garden_log
from user_management.models import Forums, Replies, Likes


# SETUP CLASSES:
class CommonUsers(TestCase):
    def setUp(self):
        # add a user entry
        self.test_user = User.objects.create(
            email = "test@gmail.com",
            username = "first",
            role = "user",
            zip_code = "53211"
        )


class CommonPlants(TestCase):
    def setUp(self):
        # add a plant entry
        self.test_plant = Plants.objects.create(
            species = "test species",
            variety = "test variety",
            maturity_time = 1,
            germination_time = 1,
            spacing_x = 1,
            spacing_y = 1,
            sun_level = "full sun",
            planting_depth = 1.1,
            water_req = 1.1,
            plant_description = "test description"
        )


class CommonGardens(CommonUsers):
    def setUp(self):
        super().setUp()

        # add a garden entry
        self.test_garden = Gardens.objects.create(
            user_id = self.test_user,
            name = "test garden",
            size_x = 1,
            size_y = 1
        )


class CommonLogs(CommonGardens):
    def setUp(self):
        super().setUp()

        self.test_plant = Plants.objects.create(
            species = "test species",
            variety = "test variety",
            maturity_time = 1,
            germination_time = 1,
            spacing_x = 1,
            spacing_y = 1,
            sun_level = "full sun",
            planting_depth = 1.1,
            water_req = 1.1,
            plant_description = "test description"
        )

        self.test_plant2 = Plants.objects.create(
            species = "species2",
            variety = "variety2",
            maturity_time = 2,
            germination_time = 2,
            spacing_x = 2,
            spacing_y = 2,
            sun_level = "full sun",
            planting_depth = 2.2,
            water_req = 2.2,
            plant_description = "description2"
        )

        # add a valid garden_log entry
        self.test_log = Garden_log.objects.create(
            garden_id = self.test_garden,
            plant_id = self.test_plant,
            x_coordinate = 1,
            y_coordinate = 1
        )


class CommonForums(CommonUsers):
    def setUp(self):
        super().setUp()

        # create a forum entry
        self.test_forum = Forums.objects.create(
            user_id = self.test_user,
            title = "test title",
            body = "test body"
        )


class CommonReplies(CommonForums):
    def setUp(self):
        super().setUp()

        # create a reply to the initial forum post
        # note: the same user who created the forum is making a reply for test simplicity
        self.test_forum_reply = Replies.objects.create(
            user_id = self.test_user,
            forum_id = self.test_forum,
            parent_id = None,
            body = "test reply body"
        )


class CommonLikes(CommonReplies):
    def setUp(self):
        super().setUp()

        # create a like entry
        self.test_like = Likes.objects.create(
            user_id = self.test_user,
            reply_id = self.test_forum_reply,
            ld_value = 1
        )


# SCHEMA CODE TESTS:
# These are safety tests to ensure that models code was implemented according to vision
class UserSchema(CommonUsers):
    # create one user
    def test_add_user(self):
        self.assertEqual(1, User.objects.count(), "number of records in User table is incorrect.")


class PlantsSchema(CommonPlants):
    # create one plant
    def test_add_plant_all(self):
        self.assertEqual(1, Plants.objects.count(), "number of records in Plants table is incorrect.")
    
    # catches violation of maturity time >= 0
    # (note: also works as a check for all other >= 0 constraints)
    # use: tracked validity through swap of constraint for new data type
    def test_maturity_constraint(self):
        with self.assertRaises(IntegrityError, msg="negative value failed to raise error"):
            Plants.objects.create(
                species = "test species",
                variety = "test variety",
                maturity_time = -1,
                germination_time = 1,
                spacing_x = 1,
                spacing_y = 1,
                sun_level = "full sun",
                planting_depth = 1.1,
                water_req = 1.1,
                plant_description = "test description"
            )
    
    # catches violation of depth (decimal) >= 0
    # (note: also works as a check for all other decimal >= 0 constraints)
    def test_positive_depth_constraint(self):
        with self.assertRaises(IntegrityError, msg="check_depth_pos failed to raise error"):
            Plants.objects.create(
                species = "test species",
                variety = "test variety",
                maturity_time = 1,
                germination_time = 1,
                spacing_x = 1,
                spacing_y = 1,
                sun_level = "full sun",
                planting_depth = -0.01,
                water_req = 1.1,
                plant_description = "test description"
            )


class GardenSchema(CommonGardens):
    # create one garden
    def test_add_garden(self):
        self.assertEqual(1, Gardens.objects.count(), "number of records in Gardens table is incorrect.")
    
    # catches violation of size_x > 0
    # (note: also works as a check for all other > 0 constraints)
    def test_negative_x(self):
        with self.assertRaises(IntegrityError, msg="check_size_x_pos failed to raise error"):
            Gardens.objects.create(
            user_id = self.test_user,
            size_x = 0,
            size_y = 1
        )


class Garden_logSchema(CommonLogs):
    # create one garden_log entry
    def test_add_garden_log(self):
        self.assertEqual(1, Garden_log.objects.count(), "number of records in Garden_log table is incorrect.")
    
    # test log entry that violates unique key
    def test_log_unique(self):
        with self.assertRaises(IntegrityError, msg="unq_plot_space failed to raise error"):
            # add violating log entry
            Garden_log.objects.create(
                garden_id = self.test_garden,
                plant_id = self.test_plant2, # diff
                x_coordinate = 1,
                y_coordinate = 1
            )


class ForumSchema(CommonForums):
    # create one forum entry
    def test_add_forum(self):
        self.assertEqual(1, Forums.objects.count(), "number of records in Forums table is incorrect.")


class RepliesSchema(CommonReplies):    
    # create a reply directly to a forum post
    def test_add_forum_reply(self):
        self.assertEqual(1, Replies.objects.count(), "number of records in Replies table is incorrect.")
    
    # create a reply to a reply
    def test_add_reply_reply(self):
        Replies.objects.create(
            user_id = self.test_user,
            forum_id = self.test_forum,
            parent_id = self.test_forum_reply,
            body = "reply reply"
        )
        self.assertEqual(2, Replies.objects.count(), "number of records in Replies table is incorrect.")

    # ensure self-referential foreign key
    def test_reply_reply_fk(self):
        # add child entry
        child_reply = Replies.objects.create(
            user_id = self.test_user,
            forum_id = self.test_forum,
            parent_id = self.test_forum_reply,
            body = "reply reply"
        )

        # retrieve the child entry to check
        check_child = Replies.objects.get(pk=child_reply.id)

        self.assertEqual(self.test_forum_reply, check_child.parent_id, "child reply's self-referential FK is unexpected value.")


class LikesSchema(CommonLikes):
    # test that a single like entry was added correctly
    def test_add_like(self):
        self.assertEqual(1, Likes.objects.count(), "number of records in Likes table is incorrect.")
    
    # test like entry that violates unique key
    def test_likes_unique(self):
        with self.assertRaises(IntegrityError, msg="unq_vote failed to raise error"):
            Likes.objects.create(
                user_id = self.test_user,
                reply_id = self.test_forum_reply,
                ld_value = 0 # diff
            )


# UNIT TESTS
# Note: all unit tests will need to be updated to use the create methods later on
class UserUnit(CommonUsers):
    def test_user_string(self):
        self.assertEqual("test@gmail.com - ID:1", self.test_user.__str__(), "User string representation is incorrect")


class PlantsUnit(CommonPlants):
    def test_plants_string(self):
        self.assertEqual("test species - test variety", self.test_plant.__str__(), "Plants string representation is incorrect")


class GardensUnit(CommonGardens):
    def test_gardens_string(self):
        self.assertEqual("garden id:1 - size:1x1", self.test_garden.__str__(), "Gardens string representation is incorrect")


class Garden_logUnit(CommonLogs):
    def test_garden_log_string(self):
        self.assertEqual("garden:1 - plant:(test species - test variety) @ [1,1]", self.test_log.__str__(), "Garden_log string representation is incorrect")

    def test_in_bounds(self):
        self.assertTrue(self.test_log.is_in_bounds(), "is_in_bounds method returned false, but should be true")
    
    def test_out_of_bounds(self):
        # create an out of bounds garden_log entry
        test_out = Garden_log.objects.create(
            garden_id = self.test_garden,
            plant_id = self.test_plant,
            x_coordinate = 6,
            y_coordinate = 6
        )
        self.assertFalse(test_out.is_in_bounds(), "is_in_bounds method returned true, but should be false")


class ForumsUnit(CommonForums):
    def test_forums_string(self):
        self.assertEqual("Forum ID:1", self.test_forum.__str__(), "Forums string representation is incorrect")


class RepliesUnit(CommonReplies):
    def test_replies_string(self):
        self.assertEqual("Reply ID:1", self.test_forum_reply.__str__(), "Replies string representation is incorrect")


class LikesUnit(CommonLikes):
    def test_likes_string(self):
        self.assertEqual("Like ID:1", self.test_like.__str__(), "Likes string representation is incorrect")

