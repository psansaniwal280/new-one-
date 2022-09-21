import json
from django.core.files.uploadedfile import SimpleUploadedFile
from graphene_file_upload.django.testing import GraphQLFileUploadTestCase

class MutationTestCase(GraphQLFileUploadTestCase):
   def test_some_mutation(self):
        # png_hex = ['\x89', 'P', 'N', 'G', '\r', '\n', '\x1a', '\n', '\x00',
        #     '\x00', '\x00', '\r', 'I', 'H', 'D', 'R', '\x00',
        #     '\x00', '\x00', '\x01', '\x00', '\x00', '\x00', '\x01',
        #     '\x08', '\x02', '\x00', '\x00', '\x00', '\x90',
        #     'w', 'S', '\xde', '\x00', '\x00', '\x00', '\x06', 'b', 'K',
        #     'G', 'D', '\x00', '\x00', '\x00', '\x00',
        #     '\x00', '\x00', '\xf9', 'C', '\xbb', '\x7f', '\x00', '\x00',
        #     '\x00', '\t', 'p', 'H', 'Y', 's', '\x00',
        #     '\x00', '\x0e', '\xc3', '\x00', '\x00', '\x0e', '\xc3',
        #     '\x01', '\xc7', 'o', '\xa8', 'd', '\x00', '\x00',
        #     '\x00', '\x07', 't', 'I', 'M', 'E', '\x07', '\xe0', '\x05',
        #     '\r', '\x08', '%', '/', '\xad', '+', 'Z',
        #     '\x89', '\x00', '\x00', '\x00', '\x0c', 'I', 'D', 'A', 'T',
        #     '\x08', '\xd7', 'c', '\xf8', '\xff', '\xff',
        #     '?', '\x00', '\x05', '\xfe', '\x02', '\xfe', '\xdc', '\xcc',
        #     'Y', '\xe7', '\x00', '\x00', '\x00', '\x00',
        #     'I', 'E', 'N', 'D', '\xae', 'B', '`', '\x82']

        # valid_png_bin = str.encode("".join(png_hex))
        test_file = SimpleUploadedFile(name='BeachPartyItaly.mp4', content=file_text.encode('utf-8'))

        response = self.file_query( 
            '''
            mutation createPost($image: Upload!) {
                createPost(postData: {postId: 156, media: $image, title: "test post 9", postVenueId: 6, userRating: 3.4, isVerified: false, userId: 1, description: "@user1 GeeksforGeeks is a #.;23 wonderful #websit.e for #Co#@user4"}) {
                    post {
                    postId
                    media
                    title
                    postVenueId {
                        postVenueId
                    }
                    }
                }
                }
            ''',
            op_name='createPost',
            files={'image': test_file}
        )

        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)